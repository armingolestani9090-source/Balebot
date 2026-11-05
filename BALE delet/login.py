from bale.auth import login

phone = int(input("شماره بله: "))

result = login(
    phone,
    lambda: input("کد تأیید: ")
)

print("\n✅ ورود موفق بود!")
print("نام:", result.user_name)
print("آیدی:", result.user_id)
print("\nACCESS TOKEN:")
print(result.access_token)