from bale import auth


def login_account():

    print("╔══════════════════════════════════╗")
    print("║          BALE LOGIN              ║")
    print("╚══════════════════════════════════╝")
    print()

    phone = input("📱 شماره بله: ").strip()

    try:
        phone = int(phone)
    except ValueError:
        print("❌ شماره موبایل نامعتبر است.")
        return None

    try:

        print("\n⏳ در حال ارسال کد تأیید...")

        session = auth.start_phone_auth(
            phone
        )

        print("📨 کد تأیید ارسال شد.")

        code = input("🔐 کد تأیید: ").strip()

        print("\n⏳ در حال ورود...")

        result = auth.validate_code(
            session.transaction_hash,
            code
        )

        print("\n✅ ورود موفق بود!")
        print("نام:", result.user_name)
        print("آیدی:", result.user_id)

        print("\nACCESS TOKEN:")
        print(result.access_token)

        return result.access_token

    except Exception as error:

        print(
            f"\n❌ خطا در ورود: "
            f"{type(error).__name__}: {error}"
        )

        return None


if __name__ == "__main__":

    token = login_account()

    if token:
        print("\n✅ توکن را داخل config.py قرار بده.")