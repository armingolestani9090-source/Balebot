import asyncio

from bale import BaleClient
from config import BALE_ACCESS_TOKEN


async def delete_messages(client, channel, count):
    messages = await client.get_messages(
        channel,
        limit=count,
        page_size=min(count, 1000)
    )

    if not messages:
        return 0

    rids = [message.rid for message in messages]

    await client.delete_messages(channel, rids)

    return len(rids)


async def count_messages(client, channel):
    count = 0

    async for message in client.iter_messages(
        channel,
        limit=None,
        page_size=1000
    ):
        count += 1

        if count % 1000 == 0:
            print(f"📊 {count} پیام شمارش شد...")

    return count


async def main():
    client = BaleClient(BALE_ACCESS_TOKEN)

    await client.connect()

    print("✅ وصل شد")
    print("حذف: @akhbartareek 400")
    print("شمارش: @akhbartareek count")
    print("خروج: exit")
    print()

    try:
        while True:
            command = input("دستور: ").strip()

            if command.lower() == "exit":
                break

            parts = command.split()

            if len(parts) != 2:
                print("❌ فرمت اشتباه است")
                continue

            channel = parts[0]
            action = parts[1].lower()

            # شمارش
            if action == "count":
                print(f"⏳ در حال شمارش {channel} ...")

                try:
                    total = await count_messages(client, channel)
                    print(f"\n✅ تعداد کل پیام‌ها: {total}\n")
                except Exception as e:
                    print(f"❌ خطا: {e}\n")

                continue

            # حذف
            try:
                delete_count = int(action)

                if delete_count <= 0:
                    print("❌ تعداد باید بیشتر از صفر باشد")
                    continue

            except ValueError:
                print("❌ فرمت اشتباه است")
                continue

            print(f"⏳ در حال حذف {delete_count} پیام...")

            try:
                deleted = await delete_messages(
                    client,
                    channel,
                    delete_count
                )

                print(f"✅ {deleted} پیام حذف شد\n")

            except Exception as e:
                print(f"❌ خطا: {e}\n")

    finally:
        await client.disconnect()
        print("👋 برنامه بسته شد")


asyncio.run(main())