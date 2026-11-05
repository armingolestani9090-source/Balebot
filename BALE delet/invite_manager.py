# ==========================================
# Bale Invite Manager
# مدیریت مخاطبین و افزودن انتخابی کاربران
# ==========================================

from bale.bale_pb2 import (
    GroupPeer,
    UserPeer,
    GetContactsRequest,
    InviteUserRequest,
)


# ==========================================
# تبدیل کانال به GroupPeer
# ==========================================

async def get_group_peer(
    client,
    channel,
):

    info = await client.get_entity(
        channel
    )

    peer = getattr(
        info,
        "peer",
        None,
    )

    if peer is not None:

        group_id = getattr(
            peer,
            "id",
            None,
        )

        access_hash = getattr(
            peer,
            "access_hash",
            None,
        )

        if access_hash is None:

            access_hash = getattr(
                peer,
                "accessHash",
                None,
            )

    else:

        group_id = getattr(
            info,
            "id",
            None,
        )

        access_hash = getattr(
            info,
            "access_hash",
            None,
        )

        if access_hash is None:

            access_hash = getattr(
                info,
                "accessHash",
                None,
            )

    if group_id is None:

        raise ValueError(
            f"شناسه مقصد از "
            f"{type(info).__name__} "
            f"قابل استخراج نیست."
        )

    if access_hash is None:

        raise ValueError(
            "accessHash مقصد پیدا نشد."
        )

    return GroupPeer(
        groupId=int(group_id),
        accessHash=int(access_hash),
    )


# ==========================================
# دریافت مخاطبین اکانت
# ==========================================

async def get_contacts(
    client,
):

    request = GetContactsRequest(
        contactsHash=""
    )

    response = await client.call(
        "bale.users.v1.Users",
        "GetContacts",
        request=request,
    )

    if response is None:

        return []

    return list(
        getattr(
            response,
            "userPeers",
            [],
        )
    )


# ==========================================
# ساخت UserPeer
# ==========================================

def make_user_peer(
    contact,
):

    uid = getattr(
        contact,
        "uid",
        None,
    )

    access_hash = getattr(
        contact,
        "accessHash",
        None,
    )

    if uid is None:

        raise ValueError(
            "UID مخاطب پیدا نشد."
        )

    if access_hash is None:

        raise ValueError(
            f"accessHash برای UID={uid} "
            f"پیدا نشد."
        )

    return UserPeer(
        uid=int(uid),
        accessHash=int(access_hash),
    )


# ==========================================
# پیدا کردن مخاطب بر اساس UID
# ==========================================

def find_contact_by_uid(
    contacts,
    uid,
):

    target_uid = int(uid)

    for contact in contacts:

        contact_uid = getattr(
            contact,
            "uid",
            None,
        )

        if contact_uid is None:

            continue

        if int(contact_uid) == target_uid:

            return contact

    return None


# ==========================================
# پیدا کردن چند UID انتخاب‌شده
# ==========================================

def find_selected_contacts(
    contacts,
    user_ids,
):

    selected = []
    not_found = []

    seen = set()

    for raw_uid in user_ids:

        try:

            uid = int(raw_uid)

        except (TypeError, ValueError):

            not_found.append(
                str(raw_uid)
            )

            continue

        if uid <= 0:

            not_found.append(
                str(uid)
            )

            continue

        if uid in seen:

            continue

        seen.add(uid)

        contact = find_contact_by_uid(
            contacts,
            uid,
        )

        if contact is None:

            not_found.append(
                str(uid)
            )

            continue

        selected.append(
            contact
        )

    return selected, not_found


# ==========================================
# ارسال درخواست InviteUser
# ==========================================

async def send_invite_request(
    client,
    channel,
    uid,
    access_hash,
):

    # --------------------------------------
    # شناسایی مقصد
    # --------------------------------------

    group_peer = await get_group_peer(
        client,
        channel,
    )

    # --------------------------------------
    # ساخت UserPeer
    # --------------------------------------

    user_peer = UserPeer(
        uid=int(uid),
        accessHash=int(access_hash),
    )

    # --------------------------------------
    # ساخت درخواست
    # --------------------------------------

    request = InviteUserRequest(
        groupPeer=group_peer,
        user=user_peer,
        rid=0,
    )

    # --------------------------------------
    # ارسال درخواست
    # --------------------------------------

    result = await client.call(
        "bale.groups.v1.Groups",
        "InviteUser",
        request=request,
    )

    return result


# ==========================================
# دعوت یک کاربر مشخص
#
# @channel inviteuser UID
# ==========================================

async def invite_user(
    client,
    channel,
    uid,
    access_hash=None,
):

    print(
        f"⏳ در حال پردازش UID={uid} "
        f"برای {channel}..."
    )

    # --------------------------------------
    # اعتبارسنجی UID
    # --------------------------------------

    try:

        uid = int(uid)

    except (TypeError, ValueError):

        print(
            f"❌ UID نامعتبر: {uid}"
        )

        return False

    if uid <= 0:

        print(
            f"❌ UID باید بیشتر از صفر باشد."
        )

        return False

    # --------------------------------------
    # اگر accessHash نداریم،
    # از مخاطبین اکانت پیدا می‌کنیم
    # --------------------------------------

    if access_hash is None:

        print(
            "⏳ در حال دریافت مخاطبین اکانت..."
        )

        try:

            contacts = await get_contacts(
                client
            )

        except Exception as error:

            print(
                f"❌ خطا در دریافت مخاطبین: "
                f"{type(error).__name__}: "
                f"{error}"
            )

            return False

        if not contacts:

            print(
                "❌ هیچ مخاطبی دریافت نشد."
            )

            return False

        print(
            f"👥 تعداد مخاطبین اکانت: "
            f"{len(contacts)}"
        )

        contact = find_contact_by_uid(
            contacts,
            uid,
        )

        if contact is None:

            print(
                f"❌ UID={uid} "
                f"در مخاطبین اکانت پیدا نشد."
            )

            return False

        access_hash = getattr(
            contact,
            "accessHash",
            None,
        )

        if access_hash is None:

            print(
                f"❌ accessHash برای UID={uid} "
                f"پیدا نشد."
            )

            return False

        print(
            f"✅ UID={uid} در مخاطبین پیدا شد."
        )

    # --------------------------------------
    # اعتبارسنجی accessHash
    # --------------------------------------

    try:

        access_hash = int(
            access_hash
        )

    except (TypeError, ValueError):

        print(
            f"❌ accessHash نامعتبر است."
        )

        return False

    # --------------------------------------
    # ارسال درخواست
    # --------------------------------------

    print(
        "⏳ در حال ارسال درخواست به سرور..."
    )

    try:

        result = await send_invite_request(
            client,
            channel,
            uid,
            access_hash,
        )

        print(
            "📡 پاسخ واقعی سرور:"
        )

        print(
            result
        )

        print(
            f"ℹ️ درخواست InviteUser برای "
            f"UID={uid} ارسال شد."
        )

        print(
            "ℹ️ پاسخ RPC به‌تنهایی تأیید "
            "عضویت قطعی کاربر نیست."
        )

        return True

    except Exception as error:

        print(
            f"❌ UID={uid} ناموفق بود: "
            f"{type(error).__name__}: "
            f"{error}"
        )

        return False


# ==========================================
# دعوت چند مخاطب اکانت
#
# @channel invite 100
# ==========================================

async def invite_members(
    client,
    channel,
    count,
):

    print(
        "⏳ در حال دریافت مخاطبین اکانت..."
    )

    try:

        contacts = await get_contacts(
            client
        )

    except Exception as error:

        print(
            f"❌ خطا در دریافت مخاطبین: "
            f"{type(error).__name__}: "
            f"{error}"
        )

        return

    if not contacts:

        print(
            "❌ هیچ مخاطبی پیدا نشد."
        )

        return

    # --------------------------------------
    # اعتبارسنجی تعداد
    # --------------------------------------

    try:

        count = int(count)

    except (TypeError, ValueError):

        print(
            "❌ تعداد مخاطب نامعتبر است."
        )

        return

    if count <= 0:

        print(
            "❌ تعداد باید بیشتر از صفر باشد."
        )

        return

    contacts = contacts[:count]

    print(
        f"👥 مخاطبین قابل بررسی: "
        f"{len(contacts)}"
    )

    # --------------------------------------
    # شناسایی مقصد
    # --------------------------------------

    try:

        group_peer = await get_group_peer(
            client,
            channel,
        )

    except Exception as error:

        print(
            f"❌ خطا در شناسایی مقصد: "
            f"{type(error).__name__}: "
            f"{error}"
        )

        return

    success = 0
    failed = 0

    print(
        "⏳ شروع پردازش مخاطبین..."
    )

    # --------------------------------------
    # پردازش مخاطبین
    # --------------------------------------

    for index, contact in enumerate(
        contacts,
        start=1,
    ):

        try:

            user_peer = make_user_peer(
                contact
            )

            uid = int(
                user_peer.uid
            )

            access_hash = int(
                user_peer.accessHash
            )

            print()

            print(
                f"👤 مخاطب "
                f"{index}/{len(contacts)}"
            )

            print(
                f"   UID: {uid}"
            )

            # ----------------------------------
            # ساخت درخواست
            # ----------------------------------

            request = InviteUserRequest(
                groupPeer=group_peer,
                user=user_peer,
                rid=0,
            )

            # ----------------------------------
            # ارسال درخواست
            # ----------------------------------

            result = await client.call(
                "bale.groups.v1.Groups",
                "InviteUser",
                request=request,
            )

            print(
                "📡 پاسخ InviteUser:"
            )

            print(
                result
            )

            success += 1

            print(
                f"ℹ️ درخواست UID={uid} "
                f"ارسال شد."
            )

        except Exception as error:

            failed += 1

            print(
                f"❌ مخاطب "
                f"{index}/{len(contacts)} "
                f"ناموفق بود: "
                f"{type(error).__name__}: "
                f"{error}"
            )

    # --------------------------------------
    # نتیجه
    # --------------------------------------

    print()

    print(
        "=========================================="
    )

    print(
        "📊 نتیجه عملیات"
    )

    print(
        "=========================================="
    )

    print(
        f"👥 بررسی‌شده: "
        f"{len(contacts)}"
    )

    print(
        f"📡 درخواست‌های ارسال‌شده: "
        f"{success}"
    )

    print(
        f"❌ ناموفق: "
        f"{failed}"
    )

    print(
        "=========================================="
    )


# ==========================================
# دعوت فقط UIDهای انتخاب‌شده
#
# @channel inviteids UID UID UID
# ==========================================

async def invite_selected_users(
    client,
    channel,
    user_ids,
):

    # --------------------------------------
    # اعتبارسنجی
    # --------------------------------------

    if not user_ids:

        print(
            "❌ هیچ UIDای وارد نشده."
        )

        return

    normalized_ids = []

    for raw_uid in user_ids:

        try:

            uid = int(raw_uid)

        except (TypeError, ValueError):

            print(
                f"❌ UID نامعتبر: {raw_uid}"
            )

            continue

        if uid <= 0:

            print(
                f"❌ UID نامعتبر: {uid}"
            )

            continue

        if uid not in normalized_ids:

            normalized_ids.append(
                uid
            )

    if not normalized_ids:

        print(
            "❌ هیچ UID معتبر وجود ندارد."
        )

        return

    # --------------------------------------
    # دریافت مخاطبین
    # --------------------------------------

    print(
        "⏳ در حال دریافت مخاطبین اکانت..."
    )

    try:

        contacts = await get_contacts(
            client
        )

    except Exception as error:

        print(
            f"❌ خطا در دریافت مخاطبین: "
            f"{type(error).__name__}: "
            f"{error}"
        )

        return

    if not contacts:

        print(
            "❌ هیچ مخاطبی از اکانت دریافت نشد."
        )

        return

    print(
        f"👥 تعداد مخاطبین اکانت: "
        f"{len(contacts)}"
    )

    # --------------------------------------
    # پیدا کردن UIDهای انتخاب‌شده
    # --------------------------------------

    selected, not_found = find_selected_contacts(
        contacts,
        normalized_ids,
    )

    print()

    print(
        f"🎯 UIDهای انتخاب‌شده: "
        f"{len(normalized_ids)}"
    )

    print(
        f"✅ پیدا‌شده در مخاطبین: "
        f"{len(selected)}"
    )

    print(
        f"❌ پیدا‌نشده: "
        f"{len(not_found)}"
    )

    if not_found:

        print()

        print(
            "⚠️ UIDهای زیر در مخاطبین "
            "پیدا نشدند:"
        )

        for uid in not_found:

            print(
                f"   - {uid}"
            )

    if not selected:

        print(
            "\n❌ هیچ UID انتخاب‌شده‌ای "
            "در مخاطبین پیدا نشد."
        )

        return

    # --------------------------------------
    # شناسایی مقصد فقط یک بار
    # --------------------------------------

    print(
        "\n⏳ در حال شناسایی مقصد..."
    )

    try:

        group_peer = await get_group_peer(
            client,
            channel,
        )

    except Exception as error:

        print(
            f"❌ خطا در شناسایی مقصد: "
            f"{type(error).__name__}: "
            f"{error}"
        )

        return

    # --------------------------------------
    # پردازش UIDهای انتخاب‌شده
    # --------------------------------------

    success = 0
    failed = 0

    print(
        "\n=========================================="
    )

    print(
        "🚀 شروع پردازش UIDهای انتخاب‌شده"
    )

    print(
        "=========================================="
    )

    for index, contact in enumerate(
        selected,
        start=1,
    ):

        try:

            user_peer = make_user_peer(
                contact
            )

            uid = int(
                user_peer.uid
            )

            access_hash = int(
                user_peer.accessHash
            )

            print()

            print(
                f"👤 {index}/{len(selected)}"
            )

            print(
                f"   UID: {uid}"
            )

            print(
                f"   AccessHash: {access_hash}"
            )

            print(
                f"⏳ در حال پردازش UID={uid} "
                f"برای {channel}..."
            )

            # ----------------------------------
            # ساخت درخواست
            # ----------------------------------

            request = InviteUserRequest(
                groupPeer=group_peer,
                user=user_peer,
                rid=0,
            )

            # ----------------------------------
            # ارسال درخواست
            # ----------------------------------

            print(
                "⏳ در حال ارسال درخواست به سرور..."
            )

            result = await client.call(
                "bale.groups.v1.Groups",
                "InviteUser",
                request=request,
            )

            print(
                "📡 پاسخ واقعی سرور:"
            )

            print(
                result
            )

            success += 1

            print(
                f"ℹ️ درخواست برای UID={uid} "
                f"به سرور ارسال شد."
            )

        except Exception as error:

            failed += 1

            print(
                f"❌ UID={getattr(contact, 'uid', '?')} "
                f"ناموفق بود: "
                f"{type(error).__name__}: "
                f"{error}"
            )

    # --------------------------------------
    # نتیجه نهایی
    # --------------------------------------

    print()

    print(
        "=========================================="
    )

    print(
        "📊 نتیجه نهایی"
    )

    print(
        "=========================================="
    )

    print(
        f"🎯 انتخاب‌شده: "
        f"{len(normalized_ids)}"
    )

    print(
        f"👥 پیدا‌شده در مخاطبین: "
        f"{len(selected)}"
    )

    print(
        f"📡 درخواست‌های ارسال‌شده: "
        f"{success}"
    )

    print(
        f"❌ ناموفق: "
        f"{failed}"
    )

    print(
        f"⚠️ پیدا‌نشده: "
        f"{len(not_found)}"
    )

    print(
        "=========================================="
    )