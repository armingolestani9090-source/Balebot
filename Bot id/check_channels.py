import asyncio

from bale import BaleClient, pb

from config import BALE_ACCESS_TOKEN


# ==========================================
# کانال‌هایی که می‌خوایم تست کنیم
# ==========================================

CHANNELS = [
    "@bdhjdndhdjdbdb",
    "@bdhdnbdnd",
    "@ble_pakat0",
    "@hhgdrt",
]


# ==========================================
# تست مستقیم SearchPeer
# ==========================================

async def check_username(client, username):

    username = username.lstrip("@").strip()

    print()
    print("=" * 45)
    print(f"🔎 تست: @{username}")
    print("=" * 45)

    # --------------------------------------
    # 1. SearchPeer
    # --------------------------------------

    req = pb.SearchPeerRequest()

    req.query.add().searchPeerTypeCondition.peerType = 2
    req.query.add().searchPieceText.query = username.encode("utf-8")

    try:
        resp = await client.call(
            "bale.search.v1.Search",
            "SearchPeer",
            req,
            timeout=10,
        )
    except Exception as e:
        print(f"❌ SearchPeer ERROR: {type(e).__name__}: {e}")
        return

    if resp is None:
        print("⚠️ SearchPeer → پاسخ خالی")
        return

    results = list(getattr(resp, "searchResults", []) or [])

    print(f"📦 تعداد نتیجه SearchPeer: {len(results)}")

    if not results:
        print("⚠️ SearchPeer هیچ نتیجه‌ای نداد.")
        print("❗ این به‌تنهایی یعنی آزاد بودن username نیست.")
        return

    # --------------------------------------
    # 2. بررسی نتایج
    # --------------------------------------

    for index, result in enumerate(results[:5], 1):

        print()
        print(f"📌 نتیجه {index}")

        try:
            # از همان تابع داخلی کتابخانه استفاده می‌کنیم
            from bale.client import _info_from_search_result

            info = _info_from_search_result(result)

            peer = info.peer

            print(f"   نوع: {peer.kind}")
            print(f"   ID: {peer.id}")
            print(f"   AccessHash: {peer.access_hash}")

            # ----------------------------------
            # 3. GetFullGroup
            # ----------------------------------

            if peer.is_channel:

                full_req = pb.GetFullGroupRequest()

                full_req.peer.groupId = peer.id
                full_req.peer.accessHash = peer.access_hash

                try:
                    full_resp = await client.call(
                        "bale.groups.v1.Groups",
                        "GetFullGroup",
                        full_req,
                        timeout=10,
                    )

                    if full_resp is None:
                        print("   ⚠️ GetFullGroup → پاسخ خالی")
                        continue

                    # تبدیل پاسخ به PeerInfo
                    from bale.client import _info_from_full_group

                    full_info = _info_from_full_group(
                        peer,
                        full_resp
                    )

                    print(f"   Username واقعی: @{full_info.username}")

                    if (
                        full_info.username
                        and full_info.username.lower()
                        == username.lower()
                    ):
                        print("   🔴 MATCH → این username واقعاً وجود دارد")
                    else:
                        print("   🟡 نتیجه پیدا شد ولی username یکی نیست")

                except Exception as e:
                    print(
                        f"   ❌ GetFullGroup ERROR: "
                        f"{type(e).__name__}: {e}"
                    )

            else:
                print("   ⚠️ نتیجه کانال نیست.")

        except Exception as e:
            print(
                f"   ❌ پردازش نتیجه خطا داد: "
                f"{type(e).__name__}: {e}"
            )


# ==========================================
# MAIN
# ==========================================

async def main():

    print("=" * 45)
    print("       BALE USERNAME RAW CHECK")
    print("=" * 45)

    print()
    print("⏳ اتصال به بله...")

    client = BaleClient(BALE_ACCESS_TOKEN)

    try:

        await client.connect()

        print("✅ اتصال برقرار شد.")

        for username in CHANNELS:
            await check_username(client, username)

    finally:

        await client.close()

        print()
        print("👋 تست تمام شد.")


if __name__ == "__main__":
    asyncio.run(main())