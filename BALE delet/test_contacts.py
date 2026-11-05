# ==========================================
# Bale - Contacts Test
# دریافت و بررسی مخاطبین اکانت
# ==========================================

import asyncio

from bale import BaleClient
from config import BALE_ACCESS_TOKEN

from bale.bale_pb2 import (
    GetContactsRequest,
)


# ==========================================
# دریافت مخاطبین
# ==========================================

async def main():

    client = BaleClient(
        BALE_ACCESS_TOKEN
    )

    await client.connect()

    try:

        print(
            "⏳ در حال دریافت مخاطبین..."
        )

        request = GetContactsRequest(
            contactsHash=""
        )

        response = await client.call(
            "bale.users.v1.Users",
            "GetContacts",
            request=request,
        )

        print()
        print(
            "✅ پاسخ دریافت شد"
        )

        print()

        print(
            "👥 تعداد users:",
            len(response.users)
        )

        print(
            "👥 تعداد userPeers:",
            len(response.userPeers)
        )

        print()

        print(
            "===== USER PEERS ====="
        )

        for index, peer in enumerate(
            response.userPeers,
            start=1,
        ):

            uid = getattr(
                peer,
                "uid",
                None,
            )

            access_hash = getattr(
                peer,
                "accessHash",
                None,
            )

            print(
                f"{index}. "
                f"uid={uid} | "
                f"accessHash={access_hash}"
            )

            # فقط اطلاعات خام چند مخاطب اول
            if index <= 3:

                print(
                    "RAW PEER:"
                )

                print(
                    peer
                )

                print()

    except Exception as error:

        print(
            f"❌ خطا: "
            f"{type(error).__name__}: "
            f"{error}"
        )

    finally:

        await client.disconnect()


# ==========================================
# اجرا
# ==========================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )