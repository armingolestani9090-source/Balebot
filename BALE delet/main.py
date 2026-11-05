import asyncio

from bale import BaleClient

from config import BALE_ACCESS_TOKEN

from member_manager import delete_members

from invite_manager import (
    invite_members,
    invite_user,
    invite_selected_users,
)


# ==========================================
# رنگ‌ها
# ==========================================

RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"


# ==========================================
# تنظیمات
# ==========================================

MAX_DELETE = 400
PAGE_SIZE = 100


# ==========================================
# نمایش
# ==========================================

def show(
    color,
    text,
):

    print(
        f"{color}{text}{RESET}"
    )


# ==========================================
# شمارش پیام‌ها
# ==========================================

async def count_messages(
    client,
    channel,
):

    count = 0

    async for message in client.iter_messages(
        channel,
        limit=None,
        page_size=PAGE_SIZE,
    ):

        count += 1

        if count % 500 == 0:

            show(
                CYAN,
                f"📊 تعداد بررسی‌شده: {count:,}",
            )

    return count


# ==========================================
# دریافت پیام‌ها
# ==========================================

async def get_messages(
    client,
    channel,
    count,
):

    messages = await client.get_messages(
        channel,
        limit=count,
        page_size=min(
            count,
            PAGE_SIZE,
        ),
    )

    unique = []
    seen = set()

    for message in messages:

        rid = int(
            message.rid
        )

        if rid not in seen:

            seen.add(rid)

            unique.append(
                message
            )

    return unique


# ==========================================
# حذف پیام‌ها
# ==========================================

async def delete_messages(
    client,
    channel,
    count,
):

    show(
        YELLOW,
        f"⏳ در حال دریافت پیام‌های {channel}...",
    )

    messages = await get_messages(
        client,
        channel,
        count,
    )

    if not messages:

        show(
            RED,
            "❌ هیچ پیامی دریافت نشد.",
        )

        return

    rids = [
        int(message.rid)
        for message in messages
    ]

    show(
        BLUE,
        f"📨 پیام‌های دریافت‌شده: {len(rids)}",
    )

    show(
        CYAN,
        f"🆔 شناسه اولین پیام: {rids[0]}",
    )

    show(
        YELLOW,
        "⏳ در حال ارسال درخواست حذف...",
    )

    deleted_candidates = 0
    failed = 0

    for start in range(
        0,
        len(rids),
        PAGE_SIZE,
    ):

        batch = rids[
            start:start + PAGE_SIZE
        ]

        try:

            result = await client.delete_messages(
                channel,
                batch,
                revoke=True,
            )

            show(
                CYAN,
                f"📡 دسته "
                f"{start // PAGE_SIZE + 1}: "
                f"{len(batch)} پیام؛ "
                f"پاسخ: {result!r}",
            )

            deleted_candidates += len(
                batch
            )

        except Exception as error:

            failed += len(
                batch
            )

            show(
                RED,
                f"❌ خطا در دسته "
                f"{start // PAGE_SIZE + 1}: "
                f"{type(error).__name__}: "
                f"{error}",
            )

        await asyncio.sleep(
            0.3
        )

    show(
        YELLOW,
        "🔎 در حال بررسی نتیجه حذف...",
    )

    try:

        remaining = await get_messages(
            client,
            channel,
            min(
                count,
                PAGE_SIZE,
            ),
        )

        remaining_ids = {
            int(message.rid)
            for message in remaining
        }

        still_visible = [
            rid
            for rid in rids
            if rid in remaining_ids
        ]

        show(
            CYAN,
            f"📨 تعداد ارسال‌شده برای حذف: "
            f"{deleted_candidates}",
        )

        show(
            RED if failed else GREEN,
            f"❌ پیام‌های دسته‌های خطادار: "
            f"{failed}",
        )

        if still_visible:

            show(
                YELLOW,
                f"⚠️ تعداد {len(still_visible)} "
                f"شناسه هنوز در دریافت مجدد دیده شد.",
            )

            show(
                YELLOW,
                "این بررسی فقط وضعیت قابل مشاهده را نشان می‌دهد؛ "
                "نتیجه نهایی را در خود کانال هم بررسی کن.",
            )

        else:

            show(
                GREEN,
                "✅ شناسه‌های انتخاب‌شده در دریافت مجدد دیده نشدند؛ "
                "کانال را هم بررسی کن.",
            )

    except Exception as error:

        show(
            YELLOW,
            f"⚠️ بررسی مجدد ناموفق بود: "
            f"{type(error).__name__}: {error}",
        )


# ==========================================
# برنامه اصلی
# ==========================================

async def main():

    client = BaleClient(
        BALE_ACCESS_TOKEN
    )

    show(
        CYAN,
        BOLD + "╔══════════════════════════════╗",
    )

    show(
        CYAN,
        BOLD + "║       BALE MESSAGE TOOL      ║",
    )

    show(
        CYAN,
        BOLD + "╚══════════════════════════════╝",
    )

    try:

        # ==========================================
        # اتصال
        # ==========================================

        show(
            YELLOW,
            "⏳ در حال اتصال به بله...",
        )

        await client.connect()

        show(
            GREEN,
            "✅ اتصال برقرار شد!\n",
        )

        # ==========================================
        # دستورات
        # ==========================================

        show(
            BLUE,
            "دستورات:",
        )

        show(
            GREEN,
            "@channel count              شمارش پیام‌ها",
        )

        show(
            RED,
            "@channel 100                حذف ۱۰۰ پیام",
        )

        show(
            YELLOW,
            "@channel delet 100         حذف ۱۰۰ عضو",
        )

        show(
            CYAN,
            "@channel invite 100        دعوت مخاطبین",
        )

        show(
            CYAN,
            "@channel inviteuser UID    پردازش یک UID",
        )

        show(
            CYAN,
            "@channel inviteids UID...  انتخاب دستی UIDها",
        )

        show(
            YELLOW,
            f"حداکثر حذف پیام در هر دستور: "
            f"{MAX_DELETE} پیام",
        )

        show(
            YELLOW,
            "exit                       خروج",
        )

        print()

        # ==========================================
        # حلقه اصلی
        # ==========================================

        while True:

            try:

                command = input(
                    f"{BOLD}{CYAN}Bale > {RESET}"
                ).strip()

                if command.lower() == "exit":

                    break

                if not command:

                    continue

                parts = command.split()

                # ==========================================
                # دستورهای دو بخشی
                #
                # @channel count
                # @channel 100
                # ==========================================

                if len(parts) == 2:

                    channel = parts[0]

                    action = parts[1].lower()

                    # ==========================================
                    # شمارش پیام‌ها
                    # ==========================================

                    if action == "count":

                        show(
                            YELLOW,
                            f"⏳ در حال شمارش "
                            f"{channel}...",
                        )

                        total = await count_messages(
                            client,
                            channel,
                        )

                        show(
                            GREEN,
                            f"✅ تعداد پیام‌های "
                            f"شمارش‌شده: "
                            f"{total:,}\n",
                        )

                        continue

                    # ==========================================
                    # حذف پیام‌ها
                    # ==========================================

                    try:

                        delete_count = int(
                            action
                        )

                        if delete_count <= 0:

                            show(
                                RED,
                                "❌ تعداد باید بیشتر از صفر باشد.",
                            )

                            continue

                    except ValueError:

                        show(
                            RED,
                            "❌ دستور نامعتبر است.",
                        )

                        continue

                    if delete_count > MAX_DELETE:

                        show(
                            YELLOW,
                            f"⚠️ تعداد به سقف "
                            f"{MAX_DELETE} پیام محدود شد.",
                        )

                        delete_count = MAX_DELETE

                    show(
                        YELLOW,
                        f"⚠️ درخواست حذف حداکثر "
                        f"{delete_count} پیام "
                        f"از {channel}",
                    )

                    confirm = input(
                        "برای تأیید دقیقاً YES بنوی: "
                    ).strip()

                    if confirm != "YES":

                        show(
                            YELLOW,
                            "عملیات لغو شد.\n",
                        )

                        continue

                    await delete_messages(
                        client,
                        channel,
                        delete_count,
                    )

                    print()

                    continue

                # ==========================================
                # دستورات سه بخشی
                # ==========================================

                if len(parts) == 3:

                    channel = parts[0]

                    action = parts[1].lower()

                    # ==========================================
                    # پردازش یک UID
                    #
                    # @channel inviteuser UID
                    # ==========================================

                    if action == "inviteuser":

                        try:

                            uid = int(
                                parts[2]
                            )

                            if uid <= 0:

                                show(
                                    RED,
                                    "❌ UID باید بیشتر از صفر باشد.",
                                )

                                continue

                        except ValueError:

                            show(
                                RED,
                                "❌ UID باید یک عدد معتبر باشد.",
                            )

                            continue

                        show(
                            YELLOW,
                            f"⚠️ UID انتخاب‌شده: "
                            f"{uid}",
                        )

                        show(
                            YELLOW,
                            f"⚠️ مقصد: "
                            f"{channel}",
                        )

                        show(
                            CYAN,
                            "ℹ️ UID باید در مخاطبین اکانت "
                            "وجود داشته باشد.",
                        )

                        confirm = input(
                            "برای تأیید دقیقاً YES بنوی: "
                        ).strip()

                        if confirm != "YES":

                            show(
                                YELLOW,
                                "عملیات لغو شد.\n",
                            )

                            continue

                        try:

                            # --------------------------------------
                            # مهم:
                            # به‌جای ارسال UID خام به InviteUser،
                            # از invite_selected_users استفاده می‌کنیم.
                            #
                            # این تابع خودش مخاطب را پیدا می‌کند
                            # و accessHash واقعی همان مخاطب را می‌گیرد.
                            # --------------------------------------

                            await invite_selected_users(
                                client,
                                channel,
                                [uid],
                            )

                        except Exception as error:

                            show(
                                RED,
                                f"❌ خطا در پردازش UID: "
                                f"{type(error).__name__}: "
                                f"{error}",
                            )

                        print()

                        continue

                    # ==========================================
                    # انتخاب دستی UID
                    #
                    # @channel inviteids UID
                    # ==========================================

                    if action == "inviteids":

                        try:

                            uid = int(
                                parts[2]
                            )

                            if uid <= 0:

                                show(
                                    RED,
                                    "❌ UID باید بیشتر از صفر باشد.",
                                )

                                continue

                        except ValueError:

                            show(
                                RED,
                                "❌ UID باید یک عدد معتبر باشد.",
                            )

                            continue

                        show(
                            YELLOW,
                            f"⚠️ UID انتخاب‌شده: "
                            f"{uid}",
                        )

                        show(
                            YELLOW,
                            f"⚠️ مقصد: "
                            f"{channel}",
                        )

                        show(
                            CYAN,
                            "ℹ️ فقط همین UID بررسی می‌شود "
                            "و باید در مخاطبین اکانت وجود داشته باشد.",
                        )

                        confirm = input(
                            "برای تأیید دقیقاً YES بنوی: "
                        ).strip()

                        if confirm != "YES":

                            show(
                                YELLOW,
                                "عملیات لغو شد.\n",
                            )

                            continue

                        try:

                            await invite_selected_users(
                                client,
                                channel,
                                [uid],
                            )

                        except Exception as error:

                            show(
                                RED,
                                f"❌ خطا در پردازش UID: "
                                f"{type(error).__name__}: "
                                f"{error}",
                            )

                        print()

                        continue

                    # ==========================================
                    # دعوت مخاطبین
                    #
                    # @channel invite 100
                    # ==========================================

                    if action == "invite":

                        try:

                            invite_count = int(
                                parts[2]
                            )

                            if invite_count <= 0:

                                show(
                                    RED,
                                    "❌ تعداد باید بیشتر از صفر باشد.",
                                )

                                continue

                        except ValueError:

                            show(
                                RED,
                                "❌ تعداد مخاطب باید عدد باشد.",
                            )

                            continue

                        show(
                            YELLOW,
                            f"⚠️ درخواست پردازش "
                            f"{invite_count} مخاطب "
                            f"برای {channel}",
                        )

                        confirm = input(
                            "برای تأیید دقیقاً YES بنوی: "
                        ).strip()

                        if confirm != "YES":

                            show(
                                YELLOW,
                                "عملیات لغو شد.\n",
                            )

                            continue

                        try:

                            await invite_members(
                                client,
                                channel,
                                invite_count,
                            )

                        except Exception as error:

                            show(
                                RED,
                                f"❌ خطا در پردازش مخاطبین: "
                                f"{type(error).__name__}: "
                                f"{error}",
                            )

                        print()

                        continue

                    # ==========================================
                    # حذف اعضای کانال
                    #
                    # @channel delet 100
                    # ==========================================

                    if action != "delet":

                        show(
                            RED,
                            "❌ دستور نامعتبر است.",
                        )

                        continue

                    try:

                        member_count = int(
                            parts[2]
                        )

                        if member_count <= 0:

                            show(
                                RED,
                                "❌ تعداد باید بیشتر از صفر باشد.",
                            )

                            continue

                    except ValueError:

                        show(
                            RED,
                            "❌ تعداد ممبر باید عدد باشد.",
                        )

                        continue

                    show(
                        YELLOW,
                        f"⚠️ درخواست حذف "
                        f"{member_count} عضو "
                        f"از {channel}",
                    )

                    confirm = input(
                        "برای تأیید دقیقاً YES بنوی: "
                    ).strip()

                    if confirm != "YES":

                        show(
                            YELLOW,
                            "عملیات لغو شد.\n",
                        )

                        continue

                    try:

                        await delete_members(
                            client,
                            channel,
                            member_count,
                        )

                    except Exception as error:

                        show(
                            RED,
                            f"❌ خطا در حذف اعضا: "
                            f"{type(error).__name__}: "
                            f"{error}",
                        )

                    print()

                    continue

                # ==========================================
                # انتخاب دستی چند UID
                #
                # @channel inviteids UID UID UID
                # ==========================================

                if len(parts) >= 3:

                    channel = parts[0]

                    action = parts[1].lower()

                    if action == "inviteids":

                        raw_ids = parts[2:]

                        user_ids = []

                        invalid_ids = []

                        for raw_uid in raw_ids:

                            try:

                                uid = int(
                                    raw_uid
                                )

                                if uid <= 0:

                                    invalid_ids.append(
                                        raw_uid
                                    )

                                    continue

                                if uid not in user_ids:

                                    user_ids.append(
                                        uid
                                    )

                            except ValueError:

                                invalid_ids.append(
                                    raw_uid
                                )

                        if invalid_ids:

                            show(
                                RED,
                                "❌ UIDهای نامعتبر:",
                            )

                            for invalid_uid in invalid_ids:

                                show(
                                    RED,
                                    f"   - {invalid_uid}",
                                )

                            continue

                        if not user_ids:

                            show(
                                RED,
                                "❌ حداقل یک UID وارد کن.",
                            )

                            continue

                        print()

                        show(
                            YELLOW,
                            f"🎯 تعداد UIDهای "
                            f"انتخاب‌شده: "
                            f"{len(user_ids)}",
                        )

                        show(
                            CYAN,
                            "UIDها:",
                        )

                        for uid in user_ids:

                            show(
                                CYAN,
                                f"   - {uid}",
                            )

                        print()

                        show(
                            YELLOW,
                            f"⚠️ فقط همین UIDهای "
                            f"انتخاب‌شده در {channel} "
                            f"پردازش خواهند شد.",
                        )

                        confirm = input(
                            "برای تأیید دقیقاً YES بنوی: "
                        ).strip()

                        if confirm != "YES":

                            show(
                                YELLOW,
                                "عملیات لغو شد.\n",
                            )

                            continue

                        try:

                            await invite_selected_users(
                                client,
                                channel,
                                user_ids,
                            )

                        except Exception as error:

                            show(
                                RED,
                                f"❌ خطا در پردازش "
                                f"UIDهای انتخاب‌شده: "
                                f"{type(error).__name__}: "
                                f"{error}",
                            )

                        print()

                        continue

                # ==========================================
                # فرمت اشتباه
                # ==========================================

                show(
                    RED,
                    "❌ فرمت دستور اشتباه است.",
                )

            except KeyboardInterrupt:

                show(
                    YELLOW,
                    "\nعملیات متوقف شد.",
                )

                break

            except Exception as error:

                show(
                    RED,
                    f"❌ خطا: "
                    f"{type(error).__name__}: "
                    f"{error}",
                )

    except Exception as error:

        show(
            RED,
            f"❌ خطای اتصال: "
            f"{type(error).__name__}: "
            f"{error}",
        )

    finally:

        try:

            await client.disconnect()

        except Exception:

            pass

        show(
            CYAN,
            "👋 برنامه بسته شد.",
        )


# ==========================================
# اجرای برنامه
# ==========================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print(
            "\nبرنامه متوقف شد."
        )