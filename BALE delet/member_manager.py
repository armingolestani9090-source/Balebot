# ==========================================
# Bale Member Manager
# حذف اعضای کانال/گروه
# ==========================================

import asyncio

from bale.bale_pb2 import (
    GroupPeer,
    UserPeer,
    LoadMembersRequest,
    KickUserRequest,
)

# ==========================================
# تنظیمات
# ==========================================

PAGE_SIZE = 100

# تعداد حذف‌های همزمان
CONCURRENCY = 20


# ==========================================
# تبدیل Peer کانال به GroupPeer
# ==========================================

async def get_group_peer(client, channel):
    info = await client.get_entity(channel)

    # PeerInfo در این نسخه مستقیماً Peer ندارد
    # بنابراین اطلاعات شناسه را از خود object می‌گیریم.
    peer = getattr(info, "peer", None)

    if peer is not None:
        group_id = getattr(peer, "id", None)
        access_hash = getattr(peer, "access_hash", 1)

    else:
        group_id = getattr(info, "id", None)
        access_hash = getattr(info, "access_hash", 1)

    if group_id is None:
        raise ValueError(
            f"شناسه کانال از {type(info).__name__} قابل استخراج نیست."
        )

    return GroupPeer(
        groupId=int(group_id),
        accessHash=int(access_hash),
    )


# ==========================================
# دریافت اعضا
# ==========================================

async def load_members(client, channel, count):
    group_peer = await get_group_peer(client, channel)

    members = []
    next_token = None
    seen_tokens = set()

    while len(members) < count:

        current_limit = min(
            PAGE_SIZE,
            count - len(members),
        )

        request = LoadMembersRequest(
            group=group_peer,
            limit=current_limit,
        )

        # --------------------------------------
        # صفحه بعدی
        # --------------------------------------

        if next_token is not None:
            try:
                request.next.CopyFrom(next_token)
            except Exception:
                pass

        # --------------------------------------
        # درخواست اعضا
        # --------------------------------------

        response = await client.call(
            "bale.groups.v1.Groups",
            "LoadMembers",
            request=request,
        )

        if response is None:
            break

        # --------------------------------------
        # دریافت اعضای این صفحه
        # --------------------------------------

        batch = list(response.members)

        if not batch:
            break

        members.extend(batch)

        print(
            f"📥 دریافت اعضا: "
            f"{min(len(members), count)}/{count}"
        )

        # --------------------------------------
        # دریافت توکن صفحه بعد
        # --------------------------------------

        next_candidate = getattr(
            response,
            "next",
            None,
        )

        if next_candidate is None:
            break

        # --------------------------------------
        # تشخیص next خالی
        # --------------------------------------

        try:
            token_bytes = next_candidate.SerializeToString()
        except Exception:
            token_bytes = b""

        if not token_bytes:
            break

        # --------------------------------------
        # جلوگیری از حلقه بی‌نهایت
        # --------------------------------------

        if token_bytes in seen_tokens:
            break

        seen_tokens.add(token_bytes)

        next_token = next_candidate

    return members[:count]


# ==========================================
# حذف یک عضو
# ==========================================

async def kick_member(client, group_peer, member):

    try:
        # --------------------------------------
        # طبق protobuf:
        # Member.uid = شناسه کاربر
        # --------------------------------------

        uid = int(member.uid)

        if uid <= 0:
            raise ValueError(
                f"شناسه کاربر نامعتبر است: {uid}"
            )

        # --------------------------------------
        # ساخت UserPeer
        # --------------------------------------

        user_peer = UserPeer(
            uid=uid,
            accessHash=0,
        )

        # --------------------------------------
        # ساخت درخواست KickUser
        # --------------------------------------

        request = KickUserRequest(
            groupPeer=group_peer,
            user=user_peer,
            rid=0,
        )

        # --------------------------------------
        # ارسال RPC
        # --------------------------------------

        await client.call(
            "bale.groups.v1.Groups",
            "KickUser",
            request=request,
        )

        return True, uid, None

    except Exception as error:
        return False, getattr(member, "uid", 0), error


# ==========================================
# حذف اعضا به صورت همزمان
# ==========================================

async def delete_members_fast(
    client,
    group_peer,
    members,
):

    total = len(members)

    success = 0
    failed = 0

    # ======================================
    # Semaphore
    # ======================================

    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def worker(index, member):

        async with semaphore:

            return index, await kick_member(
                client,
                group_peer,
                member,
            )

    # ======================================
    # ساخت تمام Task ها
    # ======================================

    tasks = [
        asyncio.create_task(
            worker(index, member)
        )
        for index, member in enumerate(
            members,
            start=1,
        )
    ]

    # ======================================
    # اجرای موازی
    # ======================================

    completed = 0

    for future in asyncio.as_completed(tasks):

        index, result = await future

        ok, uid, error = result

        completed += 1

        if ok:
            success += 1

        else:
            failed += 1

        # ----------------------------------
        # نمایش پیشرفت
        # ----------------------------------

        if ok:
            print(
                f"⚡ حذف {completed}/{total} "
                f"موفق | uid={uid}"
            )

        else:
            print(
                f"❌ حذف {completed}/{total} "
                f"ناموفق | uid={uid} | "
                f"{type(error).__name__}: {error}"
            )

    return success, failed


# ==========================================
# حذف اعضا
# ==========================================

async def delete_members(client, channel, count):

    print(
        f"⏳ در حال دریافت {count} عضو از {channel}..."
    )

    # --------------------------------------
    # دریافت اعضا
    # --------------------------------------

    try:
        members = await load_members(
            client,
            channel,
            count,
        )

    except Exception as error:
        print(
            f"❌ خطا در دریافت اعضا: "
            f"{type(error).__name__}: {error}"
        )
        return

    if not members:
        print("❌ هیچ عضوی دریافت نشد.")
        return

    print(
        f"👥 اعضای دریافت‌شده: {len(members)}"
    )

    # اگر کمتر از مقدار درخواستی عضو وجود داشته باشد
    if len(members) < count:
        print(
            f"⚠️ فقط {len(members)} عضو قابل دریافت بود."
        )

    print(
        f"⚡ شروع حذف سریع با "
        f"{CONCURRENCY} درخواست همزمان..."
    )

    # --------------------------------------
    # GroupPeer
    # --------------------------------------

    try:
        group_peer = await get_group_peer(
            client,
            channel,
        )

    except Exception as error:
        print(
            f"❌ خطا در شناسایی کانال: "
            f"{type(error).__name__}: {error}"
        )
        return

    # --------------------------------------
    # حذف موازی اعضا
    # --------------------------------------

    try:

        success, failed = await delete_members_fast(
            client,
            group_peer,
            members,
        )

    except Exception as error:

        print(
            f"❌ خطای کلی هنگام حذف اعضا: "
            f"{type(error).__name__}: {error}"
        )

        return

    # --------------------------------------
    # نتیجه نهایی
    # --------------------------------------

    print()
    print(f"✅ حذف موفق: {success}")
    print(f"❌ حذف ناموفق: {failed}")

    if success:
        print(
            f"🎉 عملیات تمام شد؛ "
            f"{success} عضو با موفقیت حذف شدند."
        )