import os
import sys
import asyncio
import datetime
import random
import re
import pytz
from telethon import TelegramClient, events, functions, types
from telethon.tl.functions.channels import (
    EditBannedRequest, InviteToChannelRequest, GetParticipantsRequest,
    LeaveChannelRequest, CreateChannelRequest, JoinChannelRequest, EditAdminRequest,
    GetFullChannelRequest
)
from telethon.tl.functions.messages import (
    DeleteMessagesRequest, ExportChatInviteRequest, ImportChatInviteRequest,
    ReportSpamRequest, GetFullChatRequest
)
from telethon.tl.functions.phone import (
    CreateGroupCallRequest, DiscardGroupCallRequest
)
from telethon.tl.functions.contacts import BlockRequest, DeleteContactsRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import ChatBannedRights, ChatAdminRights, ChannelParticipantsKicked
from telethon.sessions import StringSession
from telethon.errors import (
    UserPrivacyRestrictedError, ChatAdminRequiredError, UserNotMutualContactError,
    UserChannelsTooMuchError, UserBotError, PeerFloodError, FloodWaitError, UserKickedError,
    UserAlreadyParticipantError
)

# ----------------------------------------------------
# 1. إعدادات الجلسة والحساب
# ----------------------------------------------------
API_ID = int(os.getenv("API_ID", "24576280"))
API_HASH = os.getenv("API_HASH", "2d331fea63e2dfeb0d2c2cf71a9a0cc9")
STRING_SESSION = os.getenv("STRING_SESSION", "1BJWap1wBu07FzEskKaCJiylVxxZC21khD8_2Asd0QIwqBvfR5czpoXUN7vNtzKBGwaB9oE4Q1JkKbmvDTKV4hxYTncJ_tT47rfJ-Ocw_fuKn0LaYJ2TjsO8h8GqKZcZk5Qts0el1bABmFzPDFwtfeyhfURllaau67ktlMMFQlJLLO170rh15eOFMUlcFJsIKZgxb4fx-m_Vo9nFBg-1nMdAGnKqcMnIjOvp-ioseRVeiDVWFL7g-VqCBtc5CloI-6hgAlpD80sajJ8T4hNyVt-BbF641roQPxwsNykjBZ-M6r3SeR_0B1wDQM0mwqXvwj3d0iA7yRf0L1dGhKxZyixBmnmzdNP0=")

client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH)

SOURCE_TITLE = "🇵🇹 Portuguese source 🇵🇹"
CAIRO_TZ = pytz.timezone('Africa/Cairo')
TELEGRAM_SYSTEM_IDS = {777000, 42777, 1271266}

# ----------------------------------------------------
# 2. الذاكرة والمتغيرات العامة
# ----------------------------------------------------
GBAN_SET = set()
GMUTE_SET = set()
MUTED_USERS = {}
MUTED_PMS = set()
REPLY_MAP = {}
BLOCKED_WORDS = set()

MAIN_DEV_ID = 1609075265
DEVELOPERS = {MAIN_DEV_ID} 

_env_devs = os.getenv("DEVELOPERS", "")
if _env_devs:
    for _id in _env_devs.split(","):
        if _id.strip().isdigit():
            DEVELOPERS.add(int(_id.strip()))

GAME_ACTIVE = False
GAME_PLAYERS = []
GAME_CHAT_ID = None

TIME_NAME_ACTIVE = False
TIME_NAME_TASK = None
ORIGINAL_NAME = ""

PM_PROTECTION_ACTIVE = False
APPROVED_USERS = set()
PM_WARNINGS = {}

AUTO_SAVE_MEDIA = False

SLEEP_ACTIVE = False
SLEEP_START_TIME = None

# ----------------------------------------------------
# 3. دالة التحقق واستخراج المستخدم (بالرد / اليوزر / الآيدي)
# ----------------------------------------------------
def is_sudo(event):
    return event.out or (event.sender_id in DEVELOPERS)

async def get_target_user(event):
    """
    استخراج آيدي المستخدم سواء بكتابة اليوزر أو الآيدي بعد الأمر، أو بالرد / التحويل.
    """
    args = event.text.split(maxsplit=1)
    if len(args) > 1 and args[1].strip():
        target = args[1].strip()
        if target.isdigit() or (target.startswith("-") and target[1:].isdigit()):
            return int(target)
        try:
            user = await client.get_entity(target)
            return user.id
        except Exception:
            pass
            
    if event.is_reply:
        reply = await event.get_reply_message()
        if reply:
            if reply.forward and reply.forward.sender_id:
                return reply.forward.sender_id
            if reply.sender_id:
                return reply.sender_id
                
    return None

# ----------------------------------------------------
# 4. قائمة الأوامر
# ----------------------------------------------------
ALL_COMMANDS_TEXT = f"""✦─────『 {SOURCE_TITLE} 』─────✦

• `.اوامري` ➪ عرض جميع الأوامر
• `.انتحال` ➪ انتحال حساب بالرد على رسالته (نسخ الاسم والبايو والصورة)
• `.رفع مطور` ➪ رفع مطور (بالرد/باليوزر/بالآيدي)
• `.تنزيل مطور` ➪ تنزيل مطور (بالرد/باليوزر/بالآيدي)
• `.مسح المطورين` ➪ مسح جميع المطورين المضافين
• `.المطورين` ➪ عرض قائمة المطورين
• `.تفليش` ➪ تصفية وطرد أعضاء الجروب
• `.تفعيل الوقت` ➪ إظهار الوقت بجانب اسمك بتوقيت مصر
• `.تعطيل الوقت` ➪ إيقاف الوقت ورجوع اسمك الاصلي
• `.تفعيل الحمايه` ➪ قفل الخاص وتحذير أي حد يبعت
• `.تعطيل الحمايه` ➪ إيقاف حماية الخاص
• `.قبول` ➪ السماح لشخص بالحديث في الخاص بدون تحذيرات
• `.رفض` ➪ إلغاء القبول وإرجاع التحذيرات لشخص
• `.بلوك` ➪ حظر المستخدم (بالرد/باليوزر/بالآيدي)
• `.حفظ الذاتية` ➪ حفظ صورة/فيديو ذاتية التدمير للرسائل المحفوظة
• `.تفعيل الذاتيه` ➪ حفظ ميديا الخاص والتدمير الذاتي تلقائياً
• `.تعطيل الذاتيه` ➪ إيقاف حفظ الصور تلقائياً
• `.سليب` ➪ تفعيل وضع النوم
• `.همسه` [الكلام] ➪ إرسال همسة سرية
• `.طرد` ➪ طرد عضو (بالرد/باليوزر/بالآيدي)
• `.طرد عام` ➪ طرد شخص من كل الجروبات المشتركة (بالرد/باليوزر/بالآيدي)
• `.مسح المحظورين` ➪ فك الحظر عن كل المحظورين في الجروب
• `.مسح المحظورين عام` ➪ تفريغ قائمة الحظر العام
• `.مسح المكتومين` ➪ فك الكتم عن قائمة المكتومين بالجروب
• `.مسح المكتومين عام` ➪ تفريغ قائمة الكتم العام
• `.م1` ➪ البحث والوسائط (`.بحث` ، `.صورة`)
• `.م2` ➪ الوقت والتاريخ (`.الوقت` ، `.التاريخ`)
• `.م3` ➪ إدارة الجروب والكتم (`.حظر` ، `.طرد` ، `.كتم` ، `.فك كتم` ، `.مسح المحظورين` ، `.مسح المكتومين`)
• `.م4` ➪ الردود (`.رد [كلمة] = [رد]` ، `.مسح الردود`)
• `.م5` ➪ التصفية والمسح (`.مسح [عدد]`)
• `.م6` ➪ لعبة الأحكام (`.احكام` ، `.لعب` ، `.بدء` ، `.انهاء`)
• `.م7` ➪ الحساب والآيدي (`.ايدي` ، `.فحص`)
• `.م8` ➪ الحظر العام (`.حظر عام` ، `.الغاء العام` ، `.مسح المحظورين عام` ، `.طرد عام`)
• `.م9` ➪ الكتم العام (`.كتم عام` ، `.الغاء كتم عام` ، `.مسح المكتومين عام`)
• `.م10` ➪ روابط الجروبات (`.الرابط`)
• `.م11` ➪ تغيير الاسم (`.اسم [الاسم]`)
• `.م12` ➪ البايو والوصف (`.بايو [الوصف]`)
• `.م13` ➪ حظر الكلمات (`.منع [كلمة]` ، `.قائمة المنع`)
• `.م14` ➪ المغادرة والانضمام (`.مغادرة` ، `.انضمام [رابط]`)
• `.م15` ➪ إنشاء الجروبات (`.انشاء جروب [الاسم]`)
• `.م16` ➪ الإضافة والحذف (`.ضيف [رابط]` ، `.حذف الجهات [رابط]`)
• `.م17` ➪ الحسابات المغلقة (`.تنظيف المغلقة`)
• `.م18` ➪ طرد البوتات (`.طرد البوتات`)
• `.م19` ➪ التثبيت (`.تثبيت` ، `.الغاء التثبيت`)
• `.م20` ➪ الإشراف والترقية (`.رفع مشرف` ، `.تنزيل مشرف`)
• `.م21` ➪ المكالمات الصوتية (`.افتح الكول` ، `.اقفل الكول`)
• `.م22` ➪ السبام والإنذار (`.بلاغ`)
• `.م23` ➪ المحادثات الخاصة (`.كشف الخاص`)
• `.م24` ➪ الصورة الشخصية (`.صورة البروفايل`)
• `.م25` ➪ كتم الخاصة (`.كتمخاص` ، `.فك كتمخاص`)
• `.م26` ➪ حفظ الميديا يدوي (`.حفظ` ، `.حفظ الذاتية`)
• `.م27` ➪ الرتب والاصلاحات (`.رتبتي` ، `.رتبته`)
• `.م28` ➪ النظام (`.ريستارت`)"""

# ----------------------------------------------------
# 5. أوامر المطورين والأوامر الأساسية
# ----------------------------------------------------

@client.on(events.NewMessage(pattern=r"^\.(اوامري|الاوامر)(\s+.*)?$"))
async def show_all_commands(event):
    if not is_sudo(event): return
    await (event.edit(ALL_COMMANDS_TEXT) if event.out else event.reply(ALL_COMMANDS_TEXT))

@client.on(events.NewMessage(pattern=r"^\.انتحال(\s+.*)?$"))
async def clone_user_cmd(event):
    if not is_sudo(event): return
    target_id = await get_target_user(event)

    if not target_id:
        msg = "⚠️ **حدد الحساب بالرد عليه أو باليوزر/الآيدي!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    status_msg = await (event.edit("⏳ **جاري نسخ الاسم، البايو، وصورة البروفايل...**") if event.out else event.reply("⏳ **جاري نسخ الاسم، البايو، وصورة البروفايل...**"))

    try:
        full_user = await client(GetFullUserRequest(target_id))
        user_entity = full_user.users[0]
        
        bio = full_user.full_user.about or ""
        first_name = user_entity.first_name or ""
        last_name = user_entity.last_name or ""

        await client(functions.account.UpdateProfileRequest(
            first_name=first_name,
            last_name=last_name,
            about=bio
        ))

        photos = await client.get_profile_photos(target_id, limit=1)
        if photos:
            photo_path = await client.download_media(photos[0])
            if photo_path:
                uploaded_file = await client.upload_file(photo_path)
                await client(functions.photos.UploadProfilePhotoRequest(file=uploaded_file))
                if os.path.exists(photo_path):
                    os.remove(photo_path)

        await status_msg.edit(
            f"🎭 **تم انتحال الحساب بنجاح!**\n\n"
            f"👤 **الاسم:** {first_name} {last_name}\n"
            f"📝 **البايو:** {bio if bio else 'بدون بايو'}"
        )

    except Exception as e:
        await status_msg.edit(f"❌ **حدث خطأ أثناء عملية الانتحال:**\n`{e}`")

@client.on(events.NewMessage(pattern=r"^\.رفع مطور(?:\s+(.*))?$"))
async def add_developer(event):
    if not is_sudo(event): return
    target_id = await get_target_user(event)

    if not target_id:
        msg = "⚠️ **حدد الشخص بالرد أو بالتحويل أو باليوزر/الآيدي!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    if target_id in DEVELOPERS:
        msg = "⚠️ **الشخص ده مرفوع مطور بالفعل!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    DEVELOPERS.add(target_id)
    msg = f"✅ **تم رفع الشخص مطور في السورس بنجاح!**\n🆔 الآيدي: `{target_id}`"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.تنزيل مطور(?:\s+(.*))?$"))
async def remove_developer(event):
    if not is_sudo(event): return
    target_id = await get_target_user(event)

    if not target_id:
        msg = "⚠️ **حدد الشخص بالرد أو بالتحويل أو باليوزر/الآيدي!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    if target_id in DEVELOPERS:
        DEVELOPERS.remove(target_id)
        msg = f"✅ **تم تنزيل الشخص من المطورين:** `{target_id}`"
    else:
        msg = "⚠️ **الشخص ده مش مطور من الأساس.**"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.مسح المطورين(\s+.*)?$"))
async def clear_developers(event):
    if not is_sudo(event): return
    me = await client.get_me()
    
    DEVELOPERS.clear()
    DEVELOPERS.add(MAIN_DEV_ID)
    DEVELOPERS.add(me.id)
    
    msg = "🗑️ **تم مسح جميع المطورين المضافين بنجاح المطور الأساسي وصاحب الحساب فقط المتبقيين!**"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.المطورين(\s+.*)?$"))
async def list_developers(event):
    if not is_sudo(event): return
    if not DEVELOPERS:
        msg = "ℹ️ **مفيش مطورين مرفوعين دلوقتي.**"
    else:
        devs = "\n".join([f"• `{dev_id}`" for dev_id in DEVELOPERS])
        msg = f"👑 **قائمة المطورين المرفوعين:**\n{devs}"
    await (event.edit(msg) if event.out else event.reply(msg))

# ----------------------------------------------------
# 6. أمر تفليش الجروب
# ----------------------------------------------------

@client.on(events.NewMessage(pattern=r"^\.تفليش(\s+.*)?$"))
async def taflesh_cmd(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ **الأمر ده بيشتغل جوة الجروبات بس!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    perms = await client.get_permissions(event.chat_id, event.sender_id)
    if not (perms.is_creator or perms.ban_users):
        msg = "⚠️ **معندكش صلاحية حظر الأعضاء لاستخدام الأمر ده!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    status_msg = await (event.edit("⚡ **جاري تفليش الجروب وتصفية الاعضاء...**") if event.out else event.reply("⚡ **جاري تفليش الجروب وتصفية الاعضاء...**"))

    kicked_count = 0
    failed_count = 0

    async for user in client.iter_participants(event.chat_id):
        if user.bot:
            continue

        try:
            user_perm = await client.get_permissions(event.chat_id, user.id)
            if user_perm.is_admin or user_perm.is_creator:
                continue

            await client.kick_participant(event.chat_id, user.id)
            kicked_count += 1
            await asyncio.sleep(0.05)
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except Exception:
            failed_count += 1

    await status_msg.edit(
        f"💥 **تم الانتهاء من تفليش الجروب!**\n\n"
        f"👥 **تم طرد:** `{kicked_count}`\n"
        f"❌ **فشل طرد:** `{failed_count}`"
    )

# ----------------------------------------------------
# 7. الأوامر الخاصة بالحماية والخدمات
# ----------------------------------------------------

@client.on(events.NewMessage(pattern=r"^\.همسه(?:\s+(.+))?$"))
async def whisper_cmd(event):
    if not is_sudo(event): return
    input_text = event.pattern_match.group(1)
    target = None
    whisper_text = ""

    if event.is_reply:
        reply = await event.get_reply_message()
        if reply and reply.sender_id:
            try:
                target_user = await client.get_entity(reply.sender_id)
                target = f"@{target_user.username}" if target_user.username else str(target_user.id)
                whisper_text = input_text if input_text else ""
            except Exception:
                target = str(reply.sender_id)
                whisper_text = input_text if input_text else ""
    elif input_text:
        parts = input_text.split(maxsplit=1)
        if len(parts) >= 2 and (parts[0].startswith("@") or parts[0].isdigit()):
            target = parts[0]
            whisper_text = parts[1]

    if not target or not whisper_text:
        msg = "⚠️ **طريقة استخدام أمر الهمسة:**\n• بالرد على الشخص: `.همسه الكلام`\n• أو بكتابة المعرف: `.همسه @username الكلام`"
        return await (event.edit(msg) if event.out else event.reply(msg))

    try:
        await event.delete()
        results = await client.inline_query('@whisperbot', f"{target} {whisper_text}")
        if results:
            await results[0].click(event.chat_id)
        else:
            await client.send_message(event.chat_id, "❌ **تعذر إنشاء الهمسة (البوت لم يرجع نتائج).**")
    except Exception as e:
        await client.send_message(event.chat_id, f"❌ **حدث خطأ أثناء إرسال الهمسة:** {e}")

@client.on(events.NewMessage(pattern=r"^\.تفعيل الحمايه(\s+.*)?$"))
async def enable_pm_guard(event):
    global PM_PROTECTION_ACTIVE
    if not is_sudo(event): return
    PM_PROTECTION_ACTIVE = True
    msg = "🛡️ **تم تفعيل حماية الخاص بنجاح!**\nأي حد يبعتلك رسالة ومكتوبلوش قبول هياخد تحذير، وبعد 7 تحذيرات هياخد بلوك تلقائي."
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.تعطيل الحمايه(\s+.*)?$"))
async def disable_pm_guard(event):
    global PM_PROTECTION_ACTIVE
    if not is_sudo(event): return
    PM_PROTECTION_ACTIVE = False
    msg = "🔓 **تم تعطيل حماية الخاص بنجاح!**"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.قبول(?:\s+(.*))?$"))
async def approve_user(event):
    global APPROVED_USERS
    if not is_sudo(event): return
    target_id = await get_target_user(event)
    if not target_id and event.is_private:
        target_id = event.chat_id

    if not target_id:
        msg = "⚠️ **استخدم الأمر بالرد على الشخص أو بيوزره/آيديه أو جوة شات الخاص!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    APPROVED_USERS.add(target_id)
    if target_id in PM_WARNINGS:
        del PM_WARNINGS[target_id]

    msg = f"✅ **تم قبول المستخدم [{target_id}] ومسموحله يكلمك في الخاص بدون تحذيرات.**"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.رفض(?:\s+(.*))?$"))
async def decline_user(event):
    global APPROVED_USERS
    if not is_sudo(event): return
    target_id = await get_target_user(event)
    if not target_id and event.is_private:
        target_id = event.chat_id

    if not target_id:
        msg = "⚠️ **استخدم الأمر بالرد على الشخص أو بيوزره/آيديه أو جوة شات الخاص!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    if target_id in APPROVED_USERS:
        APPROVED_USERS.remove(target_id)
        msg = f"❌ **تم إلغاء قبول المستخدم [{target_id}] وأصبح غير مسموح له بالحديث في الخاص.**"
    else:
        msg = f"⚠️ **المستخدم [{target_id}] غير مقبول من الأساس.**"

    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.بلوك(?:\s+(.*))?$"))
async def block_user_cmd(event):
    if not is_sudo(event): return
    target_id = await get_target_user(event)
    if not target_id and event.is_private:
        target_id = event.chat_id

    if not target_id:
        msg = "⚠️ **استخدم الأمر في المحادثة الخاصة أو بالرد أو باليوزر/الآيدي!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    try:
        await (event.edit("تم حظر المستخدم 🚫") if event.out else event.reply("تم حظر المستخدم 🚫"))
        await client(BlockRequest(id=target_id))
    except Exception as e:
        print(f"خطأ في تنفيذ البلوك: {e}")

@client.on(events.NewMessage(pattern=r"^\.تفعيل الذاتيه(\s+.*)?$"))
async def enable_auto_media(event):
    global AUTO_SAVE_MEDIA
    if not is_sudo(event): return
    AUTO_SAVE_MEDIA = True
    msg = "📸 **تم تفعيل حفظ صور الخاص والتدمير الذاتي تلقائياً!**\nأي ميديا تتبعتلك في الخاص هتوصل فوراً لرسائلك المحفوظة."
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.تعطيل الذاتيه(\s+.*)?$"))
async def disable_auto_media(event):
    global AUTO_SAVE_MEDIA
    if not is_sudo(event): return
    AUTO_SAVE_MEDIA = False
    msg = "🛑 **تم تعطيل حفظ الصور الذاتية تلقائياً!**"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.سليب(\s+.*)?$"))
async def enable_sleep_mode(event):
    global SLEEP_ACTIVE, SLEEP_START_TIME
    if not is_sudo(event): return
    SLEEP_ACTIVE = True
    SLEEP_START_TIME = datetime.datetime.now(CAIRO_TZ)
    msg = "😴 **تم تفعيل وضع السليب (النوم) بنجاح!**\nأول ما تبعت أي رسالة في أي مكان هيرجع يتعطل تلقائياً."
    await (event.edit(msg) if event.out else event.reply(msg))

# ----------------------------------------------------
# 8. ميزة الوقت في الاسم
# ----------------------------------------------------
async def time_name_loop():
    global TIME_NAME_ACTIVE, ORIGINAL_NAME
    while TIME_NAME_ACTIVE:
        try:
            current_time = datetime.datetime.now(CAIRO_TZ).strftime("%I:%M")
            new_name = f"{ORIGINAL_NAME} | {current_time}"
            await client(functions.account.UpdateProfileRequest(first_name=new_name))
        except asyncio.CancelledError:
            break
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"خطأ في الوقت: {e}")
        await asyncio.sleep(60)

@client.on(events.NewMessage(pattern=r"^\.تفعيل الوقت(\s+.*)?$"))
async def enable_time_name(event):
    global TIME_NAME_ACTIVE, TIME_NAME_TASK, ORIGINAL_NAME
    if not is_sudo(event): return
    if TIME_NAME_ACTIVE:
        msg = "⚠️ **ميزة عرض الوقت مفعلة بالفعل!**"
        return await (event.edit(msg) if event.out else event.reply(msg))
    
    me = await client.get_me()
    if not ORIGINAL_NAME:
        ORIGINAL_NAME = me.first_name or "User"
    
    TIME_NAME_ACTIVE = True
    TIME_NAME_TASK = asyncio.create_task(time_name_loop())
    
    msg = f"⏰ **تم تفعيل عرض الوقت بتوقيت مصر في الاسم!**\n👤 الاسم الأصلي: `{ORIGINAL_NAME}`"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.تعطيل الوقت(\s+.*)?$"))
async def disable_time_name(event):
    global TIME_NAME_ACTIVE, TIME_NAME_TASK, ORIGINAL_NAME
    if not is_sudo(event): return
    if not TIME_NAME_ACTIVE:
        msg = "⚠️ **ميزة عرض الوقت معطلة بالفعل!**"
        return await (event.edit(msg) if event.out else event.reply(msg))
    
    TIME_NAME_ACTIVE = False
    if TIME_NAME_TASK:
        TIME_NAME_TASK.cancel()
        TIME_NAME_TASK = None
    
    if ORIGINAL_NAME:
        try:
            await client(functions.account.UpdateProfileRequest(first_name=ORIGINAL_NAME))
        except Exception as e:
            print(f"خطأ في ترجيع الاسم: {e}")
            
    msg = f"🛑 **تم تعطيل عرض الوقت ورجع اسمك الأصلي:** `{ORIGINAL_NAME}`"
    await (event.edit(msg) if event.out else event.reply(msg))

# ----------------------------------------------------
# 9. أوامر الأقسام (من .م1 إلى .م28)
# ----------------------------------------------------

# --- م1 ---
@client.on(events.NewMessage(pattern=r"^\.م1(\s+.*)?$"))
async def m1(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر البحث والوسائط (`.م1`):**\n• `.صورة` [اسم الحاجه]\n• `.بحث` [نص البحث]\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.بحث\s+(.+)"))
async def search_cmd(event):
    if not is_sudo(event): return
    query = event.pattern_match.group(1)
    text = f"🔍 **جاري البحث عن:** `{query}`\n🔗 https://www.google.com/search?q={query.replace(' ', '+')}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.صورة\s+(.+)"))
async def search_photo(event):
    if not is_sudo(event): return
    query = event.pattern_match.group(1)
    status_msg = await (event.edit(f"🔍 **جاري جلب صورة لـ:** `{query}`...") if event.out else event.reply(f"🔍 **جاري جلب صورة لـ:** `{query}`..."))
    try:
        url = "https://picsum.photos/800/600"
        await client.send_file(event.chat_id, url, caption=f"🖼 **نتيجة الصورة لـ:** `{query}`\n{SOURCE_TITLE}")
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit(f"❌ **حصل مشكلة:** {e}")

# --- م2 ---
@client.on(events.NewMessage(pattern=r"^\.م2(\s+.*)?$"))
async def m2(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الوقت والتاريخ (`.م2`):**\n• `.الوقت`\n• `.التاريخ`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.الوقت(\s+.*)?$"))
async def get_time(event):
    if not is_sudo(event): return
    now = datetime.datetime.now(CAIRO_TZ)
    t = now.strftime("%I:%M:%S %p").replace("AM", "صباحاً").replace("PM", "مساءً")
    text = f"⏰ **الوقت دلوقتي بتوقيت مصر:** `{t}`"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.التاريخ(\s+.*)?$"))
async def get_date(event):
    if not is_sudo(event): return
    now = datetime.datetime.now(CAIRO_TZ)
    d = now.strftime("%Y-%m-%d")
    text = f"📅 **التاريخ النهاردة:** `{d}`"
    await (event.edit(text) if event.out else event.reply(text))

# --- م3 ---
@client.on(events.NewMessage(pattern=r"^\.م3(\s+.*)?$"))
async def m3(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر إدارة الجروب والكتم (`.م3`):**\n• `.حظر` (بالرد/باليوزر/بالآيدي)\n• `.فك حظر` (بالرد/باليوزر/بالآيدي)\n• `.طرد` (بالرد/باليوزر/بالآيدي)\n• `.كتم` (بالرد/باليوزر/بالآيدي)\n• `.فك كتم` (بالرد/باليوزر/بالآيدي)\n• `.مسح المحظورين`\n• `.مسح المكتومين`\n• `.تفليش` (تصفية الأعضاء)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.حظر(?:\s+(.*))?$"))
async def ban_user(event):
    if not is_sudo(event): return
    if event.text.startswith(".حظر عام"): return
    if not event.is_group:
        msg = "⚠️ **الأمر ده بيشتغل جوة الجروبات بس!**"
        return await (event.edit(msg) if event.out else event.reply(msg))
    
    target_id = await get_target_user(event)
    if not target_id:
        msg = "⚠️ **حدد العضو بالرد أو باليوزر أو بالآيدي!**\nمثال: `.حظر @username` أو `.حظر 12345678`"
        return await (event.edit(msg) if event.out else event.reply(msg))

    try:
        await client(EditBannedRequest(event.chat_id, target_id, ChatBannedRights(until_date=None, view_messages=True)))
        msg = f"⛔ **تم حظر العضو:** `{target_id}`"
    except Exception as e:
        msg = f"❌ **حدث خطأ أثناء الحظر:** `{e}`"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.فك حظر(?:\s+(.*))?$"))
async def unban_user(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ **الأمر ده بيشتغل جوة الجروبات بس!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    target_id = await get_target_user(event)
    if not target_id:
        msg = "⚠️ **حدد العضو بالرد أو باليوزر أو بالآيدي!**\nمثال: `.فك حظر @username` أو `.فك حظر 12345678`"
        return await (event.edit(msg) if event.out else event.reply(msg))

    try:
        await client(EditBannedRequest(event.chat_id, target_id, ChatBannedRights(until_date=None, view_messages=False)))
        msg = f"✅ **تم فك حظر العضو:** `{target_id}`"
    except Exception as e:
        msg = f"❌ **حدث خطأ أثناء فك الحظر:** `{e}`"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.طرد(?:\s+(.*))?$"))
async def kick_user(event):
    if not is_sudo(event): return
    if event.text.startswith(".طرد عام") or event.text.startswith(".طرد البوتات"): return
    if not event.is_group:
        msg = "⚠️ **الأمر ده بيشتغل جوة الجروبات بس!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    target_id = await get_target_user(event)
    if not target_id:
        msg = "⚠️ **حدد العضو بالرد أو باليوزر أو بالآيدي!**\nمثال: `.طرد @username` أو `.طرد 12345678`"
        return await (event.edit(msg) if event.out else event.reply(msg))

    try:
        await client.kick_participant(event.chat_id, target_id)
        msg = f"🥾 **تم طرد العضو بنجاح:** `{target_id}`"
    except Exception as e:
        msg = f"❌ **حدث خطأ أثناء الطرد:** `{e}`"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.مسح المحظورين(\s+.*)?$"))
async def clear_banned_group(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ **الأمر ده بيشتغل جوة الجروبات بس!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    status_msg = await (event.edit("⏳ **جاري فك الحظر عن جميع المحظورين في الجروب...**") if event.out else event.reply("⏳ **جاري فك الحظر عن جميع المحظورين في الجروب...**"))
    unbanned_count = 0
    
    try:
        async for user in client.iter_participants(event.chat_id, filter=ChannelParticipantsKicked):
            try:
                await client(EditBannedRequest(event.chat_id, user.id, ChatBannedRights(until_date=None, view_messages=False)))
                unbanned_count += 1
                await asyncio.sleep(0.1)
            except Exception:
                pass
        await status_msg.edit(f"✅ **تم مسح قائمة المحظورين وفك الحظر عن `{unbanned_count}` عضو!**")
    except Exception as e:
        await status_msg.edit(f"❌ **حدث خطأ أثناء مسح المحظورين:** {e}")

@client.on(events.NewMessage(pattern=r"^\.كتم(?:\s+(.*))?$"))
async def mute_user(event):
    if not is_sudo(event): return
    if event.text.startswith(".كتم عام") or event.text.startswith(".كتمخاص"): return

    if event.is_private:
        MUTED_PMS.add(event.chat_id)
        msg = "🔇 **تم كتم الشات الخاص ده بنجاح!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    elif event.is_group or event.is_channel:
        target_id = await get_target_user(event)
        if not target_id:
            msg = "⚠️ **حدد العضو بالرد أو باليوزر أو بالآيدي!**\nمثال: `.كتم @username` أو `.كتم 12345678`"
            return await (event.edit(msg) if event.out else event.reply(msg))

        MUTED_USERS.setdefault(event.chat_id, set()).add(target_id)
        msg = f"🔇 **تم كتم العضو:** `{target_id}`"
        return await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.فك كتم(?:\s+(.*))?$"))
async def unmute_user(event):
    if not is_sudo(event): return
    if event.text.startswith(".فك كتمخاص"): return

    if event.is_private:
        if event.chat_id in MUTED_PMS:
            MUTED_PMS.remove(event.chat_id)
            msg = "🔊 **تم فك الكتم عن المحادثة الخاصة دي!**"
        else:
            msg = "⚠️ **المحادثة دي مش مكتومة أصلاً.**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    elif event.is_group or event.is_channel:
        target_id = await get_target_user(event)
        if not target_id:
            msg = "⚠️ **حدد العضو بالرد أو باليوزر أو بالآيدي!**\nمثال: `.فك كتم @username` أو `.فك كتم 12345678`"
            return await (event.edit(msg) if event.out else event.reply(msg))

        if event.chat_id in MUTED_USERS and target_id in MUTED_USERS[event.chat_id]:
            MUTED_USERS[event.chat_id].remove(target_id)
            msg = f"🔊 **تم فك كتم العضو:** `{target_id}`"
        else:
            msg = "⚠️ **العضو ده مش مكتوم أصلاً.**"
        return await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.مسح المكتومين(\s+.*)?$"))
async def clear_muted_group(event):
    if not is_sudo(event): return
    if event.is_private:
        MUTED_PMS.clear()
        msg = "🗑️ **تم مسح كل المحادثات المكتومة في الخاص!**"
    else:
        if event.chat_id in MUTED_USERS:
            MUTED_USERS[event.chat_id].clear()
        msg = "🗑️ **تم مسح قائمة المكتومين في هذا الجروب بنجاح!**"
    await (event.edit(msg) if event.out else event.reply(msg))

# --- م4 ---
@client.on(events.NewMessage(pattern=r"^\.م4(\s+.*)?$"))
async def m4(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الردود التلقائية (`.م4`):**\n• `.رد` [الكلمة] = [الرد]\n• `.مسح الردود`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.رد\s+(.+)\s+=\s+(.+)"))
async def add_reply(event):
    if not is_sudo(event): return
    w = event.pattern_match.group(1).strip()
    a = event.pattern_match.group(2).strip()
    REPLY_MAP[w] = a
    text = f"✅ تم إضافة الرد:\n`{w}` ➔ `{a}`"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.مسح الردود(\s+.*)?$"))
async def clear_replies(event):
    if not is_sudo(event): return
    REPLY_MAP.clear()
    text = "🗑️ تم مسح كل الردود التلقائية."
    await (event.edit(text) if event.out else event.reply(text))

# --- م5 ---
@client.on(events.NewMessage(pattern=r"^\.م5(\s+.*)?$"))
async def m5(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر المسح والتنظيف (`.م5`):**\n• `.مسح` [العدد]\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.مسح\s+(\d+)$"))
async def purge_messages(event):
    if not is_sudo(event): return
    num = int(event.pattern_match.group(1))
    await event.delete()
    msgs = []
    async for msg in client.iter_messages(event.chat_id, limit=num):
        msgs.append(msg.id)
    if msgs:
        await client.delete_messages(event.chat_id, msgs)

# --- م6 ---
@client.on(events.NewMessage(pattern=r"^\.م6(\s+.*)?$"))
async def m6(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر لعبة الأحكام (`.م6`):**\n• `.احكام`\n• `.لعب` (للأعضاء)\n• `.بدء`\n• `.انهاء`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.احكام(\s+.*)?$"))
async def start_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ اللعبة دي جوة الجروبات بس!"
        return await (event.edit(msg) if event.out else event.reply(msg))
    GAME_ACTIVE = True
    GAME_PLAYERS = []
    GAME_CHAT_ID = event.chat_id
    text = "🎲 **فتحت باب الانضمام للعبة الأحكام!**\nاكتب `.لعب` عشان تدخل (آخري 10 لعيبة). واكتب `.بدء` للقرعة."
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.لعب\s*$"))
async def join_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not GAME_ACTIVE or event.chat_id != GAME_CHAT_ID: return
    sender = await event.get_sender()
    if not sender: return
    if any(p['id'] == sender.id for p in GAME_PLAYERS): return await event.reply("⚠️ انت منضم للعبة بالفعل!")
    if len(GAME_PLAYERS) >= 10: return await event.reply("❌ اكتمل العدد خلاص!")
    GAME_PLAYERS.append({'id': sender.id, 'name': sender.first_name or "عضو"})
    await event.reply(f"✅ تم دخول [{sender.first_name}](tg://user?id={sender.id}) اللعبة!")

@client.on(events.NewMessage(pattern=r"^\.بدء(\s+.*)?$"))
async def draw_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not is_sudo(event): return
    if not GAME_ACTIVE or event.chat_id != GAME_CHAT_ID:
        msg = "⚠️ اكتب `.احكام` الأول."
        return await (event.edit(msg) if event.out else event.reply(msg))
    if len(GAME_PLAYERS) < 2:
        msg = "⚠️ لازم عضوين على الأقل عشان نلعب!"
        return await (event.edit(msg) if event.out else event.reply(msg))
    chosen = random.sample(GAME_PLAYERS, 2)
    text = f"👑 **الحاكم:** [{chosen[0]['name']}](tg://user?id={chosen[0]['id']})\n⚖️ **المحكوم عليه:** [{chosen[1]['name']}](tg://user?id={chosen[1]['id']})"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.انهاء(\s+.*)?$"))
async def stop_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not is_sudo(event): return
    GAME_ACTIVE = False
    GAME_PLAYERS = []
    GAME_CHAT_ID = None
    text = "🔴 **تم إنهاء اللعبة.**"
    await (event.edit(text) if event.out else event.reply(text))

# --- م7 ---
@client.on(events.NewMessage(pattern=r"^\.م7(\s+.*)?$"))
async def m7(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر كشف الحساب والآيدي (`.م7`):**\n• `.ايدي`\n• `.فحص` (بالرد/باليوزر/بالآيدي)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.ايدي(\s+.*)?$"))
async def get_id(event):
    if not is_sudo(event): return
    target_id = await get_target_user(event)
    if target_id:
        text = f"🆔 **آيدي المستخدم:** `{target_id}`"
    else:
        text = f"🆔 **آيديك:** `{event.sender_id}`\n💬 **آيدي الشات:** `{event.chat_id}`"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.فحص(?:\s+(.*))?$"))
async def inspect_user(event):
    if not is_sudo(event): return
    target_id = await get_target_user(event)
    if not target_id:
        msg = "⚠️ **حدد العضو بالرد أو باليوزر أو بالآيدي.**"
        return await (event.edit(msg) if event.out else event.reply(msg))
    try:
        u = await client.get_entity(target_id)
        text = f"👤 **الاسم:** {u.first_name}\n🆔 **الآيدي:** `{u.id}`\n🌐 **اليوزر:** @{u.username if u.username else 'مفيش'}"
    except Exception as e:
        text = f"❌ **تعذر الفحص:** `{e}`"
    await (event.edit(text) if event.out else event.reply(text))

# --- م8 ---
@client.on(events.NewMessage(pattern=r"^\.م8(\s+.*)?$"))
async def m8(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الحظر العام (`.م8`):**\n• `.حظر عام` (بالرد/باليوزر/بالآيدي)\n• `.الغاء العام` (بالرد/باليوزر/بالآيدي)\n• `.طرد عام` (طرد الشخص من كل الجروبات)\n• `.مسح المحظورين عام`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.حظر عام(?:\s+(.*))?$"))
async def gban_user(event):
    if not is_sudo(event): return
    target_id = await get_target_user(event)
    if not target_id:
        msg = "⚠️ **حدد المستخدم بالرد أو باليوزر أو بالآيدي!**\nمثال: `.حظر عام @username` أو `.حظر عام 12345678`"
        return await (event.edit(msg) if event.out else event.reply(msg))

    GBAN_SET.add(target_id)
    text = f"🚫 **تم حظر المستخدم عام من كل الجروبات:** `{target_id}`"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.الغاء العام(?:\s+(.*))?$"))
async def ungban_user(event):
    if not is_sudo(event): return
    target_id = await get_target_user(event)
    if not target_id:
        msg = "⚠️ **حدد المستخدم بالرد أو باليوزر أو بالآيدي!**\nمثال: `.الغاء العام @username` أو `.الغاء العام 12345678`"
        return await (event.edit(msg) if event.out else event.reply(msg))

    if target_id in GBAN_SET:
        GBAN_SET.remove(target_id)
        text = f"✅ **تم فك الحظر العام عن:** `{target_id}`"
    else:
        text = "⚠️ **الشخص ده مش محظور عام أصلاً.**"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.مسح المحظورين عام(\s+.*)?$"))
async def clear_gban_list(event):
    if not is_sudo(event): return
    GBAN_SET.clear()
    msg = "🗑️ **تم مسح جميع المحظورين عام بنجاح!**"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.طرد عام(?:\s+(.*))?$"))
async def gkick_user(event):
    if not is_sudo(event): return
    target_id = await get_target_user(event)
    if not target_id:
        msg = "⚠️ **حدد الشخص بالرد أو باليوزر أو بالآيدي!**\nمثال: `.طرد عام @username` أو `.طرد عام 12345678`"
        return await (event.edit(msg) if event.out else event.reply(msg))
    
    status_msg = await (event.edit("⏳ **جاري طرد المستخدم من جميع الجروبات...**") if event.out else event.reply("⏳ **جاري طرد المستخدم من جميع الجروبات...**"))
    
    kicked_chats = 0
    dialogs = await client.get_dialogs()
    
    for d in dialogs:
        if d.is_group or d.is_channel:
            try:
                await client.kick_participant(d.id, target_id)
                kicked_chats += 1
                await asyncio.sleep(0.2)
            except Exception:
                pass
                
    await status_msg.edit(f"💥 **تم طرد المستخدم [`{target_id}`] من `{kicked_chats}` جروب/محادثة!**")

# --- م9 ---
@client.on(events.NewMessage(pattern=r"^\.م9(\s+.*)?$"))
async def m9(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الكتم العام (`.م9`):**\n• `.كتم عام` (بالرد/باليوزر/بالآيدي)\n• `.الغاء كتم عام` (بالرد/باليوزر/بالآيدي)\n• `.مسح المكتومين عام`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.كتم عام(?:\s+(.*))?$"))
async def gmute_user(event):
    if not is_sudo(event): return
    target_id = await get_target_user(event)
    if not target_id:
        msg = "⚠️ **حدد الشخص بالرد أو باليوزر أو بالآيدي!**\nمثال: `.كتم عام @username` أو `.كتم عام 12345678`"
        return await (event.edit(msg) if event.out else event.reply(msg))

    GMUTE_SET.add(target_id)
    text = f"🔇 **تم كتم المستخدم عام:** `{target_id}`"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.الغاء كتم عام(?:\s+(.*))?$"))
async def ungmute_user(event):
    if not is_sudo(event): return
    target_id = await get_target_user(event)
    if not target_id:
        msg = "⚠️ **حدد الشخص بالرد أو باليوزر أو بالآيدي!**\nمثال: `.الغاء كتم عام @username` أو `.الغاء كتم عام 12345678`"
        return await (event.edit(msg) if event.out else event.reply(msg))

    if target_id in GMUTE_SET:
        GMUTE_SET.remove(target_id)
        text = f"🔊 **تم إلغاء الكتم العام عن:** `{target_id}`"
    else:
        text = "⚠️ **الشخص ده مش مكتوم عام أصلاً.**"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.مسح المكتومين عام(\s+.*)?$"))
async def clear_gmute_list(event):
    if not is_sudo(event): return
    GMUTE_SET.clear()
    msg = "🗑️ **تم مسح جميع المكتومين عام بنجاح!**"
    await (event.edit(msg) if event.out else event.reply(msg))

# --- م10 ---
@client.on(events.NewMessage(pattern=r"^\.م10(\s+.*)?$"))
async def m10(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر روابط الجروبات (`.م10`):**\n• `.الرابط` (جلب رابط الجروب)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.الرابط(\s+.*)?$"))
async def get_link(event):
    if not is_sudo(event): return
    try:
        link = await client(ExportChatInviteRequest(event.chat_id))
        text = f"🔗 **رابط الجروب:** {link.link}"
    except Exception as e:
        text = f"❌ مش عارف أجيب الرابط: {e}"
    await (event.edit(text) if event.out else event.reply(text))

# --- م11 ---
@client.on(events.NewMessage(pattern=r"^\.م11(\s+.*)?$"))
async def m11(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر تغيير الاسم (`.م11`):**\n• `.اسم` [الاسم الجديد]\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.اسم\s+(.+)"))
async def update_name(event):
    if not is_sudo(event): return
    name = event.pattern_match.group(1)
    await client(functions.account.UpdateProfileRequest(first_name=name))
    text = f"✅ تم تغيير الاسم لـ: `{name}`"
    await (event.edit(text) if event.out else event.reply(text))

# --- م12 ---
@client.on(events.NewMessage(pattern=r"^\.م12(\s+.*)?$"))
async def m12(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر البايو (`.م12`):**\n• `.بايو` [الوصف الجديد]\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.بايو\s+(.+)"))
async def update_bio(event):
    if not is_sudo(event): return
    bio = event.pattern_match.group(1)
    await client(functions.account.UpdateProfileRequest(about=bio))
    text = f"✅ تم تغيير البايو لـ:\n`{bio}`"
    await (event.edit(text) if event.out else event.reply(text))

# --- م13 ---
@client.on(events.NewMessage(pattern=r"^\.م13(\s+.*)?$"))
async def m13(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر حظر الكلمات (`.م13`):**\n• `.منع` [الكلمة]\n• `.قائمة المنع`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.منع\s+(.+)"))
async def block_word(event):
    if not is_sudo(event): return
    word = event.pattern_match.group(1).strip()
    BLOCKED_WORDS.add(word)
    text = f"🚫 تم إضافة الكلمة لقائمة المنع: `{word}`"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.قائمة المنع(\s+.*)?$"))
async def list_blocked(event):
    if not is_sudo(event): return
    if not BLOCKED_WORDS:
        msg = "⚠️ مفيش كلمات ممنوعة دلوقتي."
    else:
        words = "\n".join([f"• `{w}`" for w in BLOCKED_WORDS])
        msg = f"📜 **الكلمات الممنوعة:**\n{words}"
    await (event.edit(msg) if event.out else event.reply(msg))

# --- م14 ---
@client.on(events.NewMessage(pattern=r"^\.م14(\s+.*)?$"))
async def m14(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر المغادرة والانضمام (`.م14`):**\n• `.مغادرة`\n• `.انضمام` [رابط أو يوزر الجروب]\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.مغادرة(\s+.*)?$"))
async def leave_chat(event):
    if not is_sudo(event): return
    await (event.edit("👋 يلا سلام، جاري المغادرة...") if event.out else event.reply("👋 يلا سلام، جاري المغادرة..."))
    await client(LeaveChannelRequest(event.chat_id))

@client.on(events.NewMessage(pattern=r"^\.انضمام\s+(.+)"))
async def join_chat(event):
    if not is_sudo(event): return
    link = event.pattern_match.group(1).strip()
    status_msg = await (event.edit("⏳ **جاري الانضمام...**") if event.out else event.reply("⏳ **جاري الانضمام...**"))
    try:
        if "joinchat/" in link or "+" in link:
            hash_val = link.split("+")[-1].split("joinchat/")[-1]
            try:
                await client(ImportChatInviteRequest(hash_val))
            except UserAlreadyParticipantError:
                pass
        else:
            username = link.split("/")[-1].replace("@", "")
            await client(JoinChannelRequest(username))
        await status_msg.edit("✅ **تم الانضمام بنجاح!**")
    except Exception as e:
        await status_msg.edit(f"❌ **مش عارف أدخل:** {e}")

# --- م15 ---
@client.on(events.NewMessage(pattern=r"^\.م15(\s+.*)?$"))
async def m15(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر إنشاء الجروبات (`.م15`):**\n• `.انشاء جروب` [الاسم]\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.انشاء جروب\s+(.+)"))
async def create_group(event):
    if not is_sudo(event): return
    title = event.pattern_match.group(1)
    await client(CreateChannelRequest(title=title, about="تم إنشاؤه عبر السورس", megagroup=True))
    text = f"✅ تم عمل الجروب بنجاح: `{title}`"
    await (event.edit(text) if event.out else event.reply(text))

# --- م16 ---
@client.on(events.NewMessage(pattern=r"^\.م16(\s+.*)?$"))
async def m16(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الإضافة والحذف للجهات (`.م16`):**\n• `.ضيف` [رابط الجروب المصدر]\n• `.حذف الجهات` [رابط الجروب]\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.(ضيف|اضافة|إضافة)(?:\s+(.+))?$"))
async def add_members_zedthon(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ **استخدم الأمر ده جوة الجروب اللي عايز تضيف فيه الأعضاء!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    target_chat = event.pattern_match.group(2)
    if not target_chat and event.is_reply:
        reply_msg = await event.get_reply_message()
        if reply_msg and reply_msg.text:
            target_chat = reply_msg.text.strip()

    if not target_chat:
        msg = "⚠️ **اكتب رابط أو معرف الجروب المصدر أو رد عليه!**\nمثال: `.ضيف @group_username`"
        return await (event.edit(msg) if event.out else event.reply(msg))

    status_msg = await (event.edit("⏳ **جاري سحب الأعضاء...**") if event.out else event.reply("⏳ **جاري سحب الأعضاء...**"))

    try:
        if "joinchat/" in target_chat or "+" in target_chat:
            hash_val = target_chat.split("+")[-1].split("joinchat/")[-1]
            try:
                updates = await client(ImportChatInviteRequest(hash_val))
                source_entity = updates.chats[0]
            except UserAlreadyParticipantError:
                source_entity = await client.get_entity(target_chat)
        else:
            username = target_chat.split("/")[-1].replace("@", "")
            source_entity = await client.get_entity(username)
    except Exception as e:
        return await status_msg.edit(f"❌ **مش عارف أوصل للجروب المصدر:**\n`{e}`")

    try:
        participants = await client.get_participants(source_entity)
    except Exception as e:
        return await status_msg.edit(f"❌ **مش عارف أسحب الأعضاء:**\n`{e}`")

    added_count = 0
    failed_count = 0
    privacy_count = 0

    await status_msg.edit(f"📊 **إجمالي الأعضاء:** `{len(participants)}`\n🚀 **بدأنا نقل الأعضاء...**")

    for user in participants:
        if user.deleted or user.bot or user.is_self:
            continue

        try:
            res = await client(InviteToChannelRequest(channel=event.chat_id, users=[user]))
            
            if hasattr(res, 'users') and res.users:
                added_count += 1
            else:
                failed_count += 1

            if added_count % 5 == 0 and added_count > 0:
                await status_msg.edit(
                    f"⚙️ **جاري الإضافة...**\n\n"
                    f"✅ **تمت إضافة:** `{added_count}`\n"
                    f"🔒 **تخطي بسبب الخصوصية:** `{privacy_count}`\n"
                    f"❌ **فشل:** `{failed_count}`"
                )

            await asyncio.sleep(3)

        except UserPrivacyRestrictedError:
            privacy_count += 1
        except (UserNotMutualContactError, UserChannelsTooMuchError, UserBotError, UserKickedError):
            failed_count += 1
        except PeerFloodError:
            await status_msg.edit("⚠️ **وقفنا إضافة:** الحساب خد تقييد مؤقت من التليجرام (PeerFlood).")
            break
        except FloodWaitError as e:
            await status_msg.edit(f"⏳ **انتظار التليجرام (FloodWait):** استنى `{e.seconds}` ثانية...")
            await asyncio.sleep(e.seconds)
        except ChatAdminRequiredError:
            await status_msg.edit("❌ **خطأ:** محتاج صلاحيات أدمن عشان تضيف أعضاء هنا.")
            break
        except Exception:
            failed_count += 1

    await status_msg.edit(
        f"✅ **خلصنا إضافة الأعضاء!**\n\n"
        f"🔹 **أنضافوا بنجاح:** `{added_count}`\n"
        f"🔒 **تخطي خصوصية:** `{privacy_count}`\n"
        f"❌ **فشل:** `{failed_count}`"
    )

@client.on(events.NewMessage(pattern=r"^\.حذف الجهات\s+(.+)"))
async def delete_added_contacts(event):
    if not is_sudo(event): return
    target = event.pattern_match.group(1).strip()
    status_msg = await (event.edit("⏳ **جاري حذفهم من جهات الاتصال...**") if event.out else event.reply("⏳ **جاري حذفهم من جهات الاتصال...**"))
    try:
        if "joinchat/" in target or "+" in target:
            hash_val = target.split("+")[-1].split("joinchat/")[-1]
            try:
                updates = await client(ImportChatInviteRequest(hash_val))
                entity = updates.chats[0]
            except UserAlreadyParticipantError:
                entity = await client.get_entity(target)
        else:
            username = target.split("/")[-1].replace("@", "")
            entity = await client.get_entity(username)

        deleted_count = 0
        failed = 0

        async for u in client.iter_participants(entity):
            if u.bot or u.deleted or u.is_self: continue
            try:
                await client(DeleteContactsRequest(id=[u.id]))
                deleted_count += 1
                await asyncio.sleep(0.3)
            except Exception: failed += 1

        await status_msg.edit(f"✅ **تم مسحهم من الجهات!**\n🗑️ اتتمسحوا: `{deleted_count}`\n❌ فشل: `{failed}`")
    except Exception as err:
        await status_msg.edit(f"❌ **حصل خطأ:**\n`{err}`")

# --- م17 ---
@client.on(events.NewMessage(pattern=r"^\.م17(\s+.*)?$"))
async def m17(event):
    if not is_sudo(event): return
    text = f"📌 **تنظيف الحسابات المغلقة (`.م17`):**\n• `.تنظيف المغلقة`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.تنظيف المغلقة(\s+.*)?$"))
async def clean_deleted(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ للجروبات بس."
        return await (event.edit(msg) if event.out else event.reply(msg))
    status_msg = await (event.edit("🔍 جاري فحص الحسابات المحذوفة...") if event.out else event.reply("🔍 جاري فحص الحسابات المحذوفة..."))
    c = 0
    async for u in client.iter_participants(event.chat_id):
        if u.deleted:
            try:
                await client(EditBannedRequest(event.chat_id, u.id, ChatBannedRights(until_date=None, view_messages=True)))
                c += 1
            except Exception: pass
    await status_msg.edit(f"🧹 تم طرد `{c}` حسابات محذوفة.")

# --- م18 ---
@client.on(events.NewMessage(pattern=r"^\.م18(\s+.*)?$"))
async def m18(event):
    if not is_sudo(event): return
    text = f"📌 **طرد البوتات (`.م18`):**\n• `.طرد البوتات`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.طرد البوتات(\s+.*)?$"))
async def purge_bots(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ للجروبات بس."
        return await (event.edit(msg) if event.out else event.reply(msg))
    status_msg = await (event.edit("🔍 جاري نفض البوتات...") if event.out else event.reply("🔍 جاري نفض البوتات..."))
    c = 0
    me = await client.get_me()
    async for u in client.iter_participants(event.chat_id):
        if u.bot and u.id != me.id:
            try:
                await client(EditBannedRequest(event.chat_id, u.id, ChatBannedRights(until_date=None, view_messages=True)))
                c += 1
            except Exception: pass
    await status_msg.edit(f"🤖 تم طرد `{c}` بوت بنجاح.")

# --- م19 ---
@client.on(events.NewMessage(pattern=r"^\.م19(\s+.*)?$"))
async def m19(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر التثبيت (`.م19`):**\n• `.تثبيت` (بالرد)\n• `.الغاء التثبيت`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.تثبيت(\s+.*)?$"))
async def pin_msg(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ رد على الرسالة."
        return await (event.edit(msg) if event.out else event.reply(msg))
    r = await event.get_reply_message()
    await client.pin_message(event.chat_id, r.id)
    msg = "📌 تم تثبيت الرسالة بنجاح."
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.الغاء التثبيت(\s+.*)?$"))
async def unpin_msg(event):
    if not is_sudo(event): return
    await client.unpin_message(event.chat_id)
    msg = "📌 تم إلغاء التثبيت."
    await (event.edit(msg) if event.out else event.reply(msg))

# --- م20 ---
@client.on(events.NewMessage(pattern=r"^\.م20(\s+.*)?$"))
async def m20(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الإشراف والترقية (`.م20`):**\n• `.رفع مشرف` (بالرد/باليوزر/بالآيدي)\n• `.تنزيل مشرف` (بالرد/باليوزر/بالآيدي)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.رفع مشرف(?:\s+(.*))?$"))
async def promote_user(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ **الأمر ده بيشتغل جوة الجروبات بس!**"
        return await (event.edit(msg) if event.out else event.reply(msg))
    
    target_id = await get_target_user(event)
    if not target_id:
        msg = "⚠️ **حدد الشخص بالرد أو باليوزر أو بالآيدي!**"
        return await (event.edit(msg) if event.out else event.reply(msg))
    
    status_msg = await (event.edit("⏳ **جاري رفع العضو مشرف...**") if event.out else event.reply("⏳ **جاري رفع العضو مشرف...**"))
    
    rights = ChatAdminRights(
        change_info=True,
        post_messages=True,
        edit_messages=True,
        delete_messages=True,
        ban_users=True,
        invite_users=True,
        pin_messages=True,
        add_admins=False,
        manage_call=True
    )
    
    try:
        await client(EditAdminRequest(
            channel=event.chat_id,
            user_id=target_id,
            admin_rights=rights,
            rank="مشرف"
        ))
        await status_msg.edit(f"👑 **تم ترقية المستخدم [`{target_id}`] مشرف بنجاح!**")
    except Exception as e:
        await status_msg.edit(f"❌ **حصل مشكلة أثناء الرفع:**\n`{e}`")

@client.on(events.NewMessage(pattern=r"^\.تنزيل مشرف(?:\s+(.*))?$"))
async def demote_user(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ **الأمر ده بيشتغل جوة الجروبات بس!**"
        return await (event.edit(msg) if event.out else event.reply(msg))
    
    target_id = await get_target_user(event)
    if not target_id:
        msg = "⚠️ **حدد الشخص بالرد أو باليوزر أو بالآيدي!**"
        return await (event.edit(msg) if event.out else event.reply(msg))
    
    status_msg = await (event.edit("⏳ **جاري تنزيل المشرف...**") if event.out else event.reply("⏳ **جاري تنزيل المشرف...**"))
    
    rights = ChatAdminRights(
        change_info=False,
        post_messages=False,
        edit_messages=False,
        delete_messages=False,
        ban_users=False,
        invite_users=False,
        pin_messages=False,
        add_admins=False,
        manage_call=False
    )
    
    try:
        await client(EditAdminRequest(
            channel=event.chat_id,
            user_id=target_id,
            admin_rights=rights,
            rank=""
        ))
        await status_msg.edit(f"📉 **تم تنزيل المستخدم [`{target_id}`] من الإشراف بنجاح!**")
    except Exception as e:
        await status_msg.edit(f"❌ **حصل مشكلة أثناء التنزيل:**\n`{e}`")

# --- م21 ---
@client.on(events.NewMessage(pattern=r"^\.م21(\s+.*)?$"))
async def m21(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر المكالمات الصوتية (`.م21`):**\n• `.افتح الكول`\n• `.اقفل الكول`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.افتح الكول(\s+.*)?$"))
async def start_group_call(event):
    if not is_sudo(event): return
    if event.is_private:
        msg = "⚠️ **الأمر ده بيشتغل جوة الجروبات والقنوات بس!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    status_msg = await (event.edit("⏳ **جاري فتح المكالمة الصوتية (الكول)...**") if event.out else event.reply("⏳ **جاري فتح المكالمة الصوتية (الكول)...**"))
    try:
        await client(CreateGroupCallRequest(peer=event.chat_id, random_id=random.randint(10000, 99999)))
        await status_msg.edit("🎙️ **تم فتح المحادثة الصوتية (الكول) بنجاح!**")
    except Exception as e:
        await status_msg.edit(f"❌ **حصل مشكلة أثناء فتح الكول:**\n`{e}`")

@client.on(events.NewMessage(pattern=r"^\.اقفل الكول(\s+.*)?$"))
async def stop_group_call(event):
    if not is_sudo(event): return
    if event.is_private:
        msg = "⚠️ **الأمر ده بيشتغل جوة الجروبات والقنوات بس!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    status_msg = await (event.edit("⏳ **جاري إغلاق المكالمة الصوتية (الكول)...**") if event.out else event.reply("⏳ **جاري إغلاق المكالمة الصوتية (الكول)...**"))
    try:
        if event.is_channel:
            full_chat = await client(GetFullChannelRequest(event.chat_id))
        else:
            full_chat = await client(GetFullChatRequest(event.chat_id))

        call = getattr(full_chat.full_chat, 'call', None)
        if not call:
            return await status_msg.edit("⚠️ **مفيش كول مفتوح حالياً في المحادثة دي عشان أقفله!**")

        await client(DiscardGroupCallRequest(call=call))
        await status_msg.edit("🛑 **تم إغلاق المحادثة الصوتية (الكول) بنجاح!**")
    except Exception as e:
        await status_msg.edit(f"❌ **حصل مشكلة أثناء إغلاق الكول:**\n`{e}`")

# --- م22 ---
@client.on(events.NewMessage(pattern=r"^\.م22(\s+.*)?$"))
async def m22(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الإبلاغ والسبام (`.م22`):**\n• `.بلاغ` (بالرد/باليوزر/بالآيدي)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.بلاغ(?:\s+(.*))?$"))
async def report_spam(event):
    if not is_sudo(event): return
    target_id = await get_target_user(event)
    if not target_id:
        msg = "⚠️ **حدد الحساب بالرد أو باليوزر/الآيدي.**"
        return await (event.edit(msg) if event.out else event.reply(msg))
    try:
        await client(ReportSpamRequest(peer=target_id))
        text = f"🚨 **بلغنا التليجرام عن الحساب:** `{target_id}`"
    except Exception as e:
        text = f"❌ **حدث خطأ:** `{e}`"
    await (event.edit(text) if event.out else event.reply(text))

# --- م23 ---
@client.on(events.NewMessage(pattern=r"^\.م23(\s+.*)?$"))
async def m23(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر المحادثات الخاصة (`.م23`):**\n• `.كشف الخاص`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.كشف الخاص(\s+.*)?$"))
async def inspect_pms(event):
    if not is_sudo(event): return
    status_msg = await (event.edit("🔍 جاري جلب أحدث الخاص...") if event.out else event.reply("🔍 جاري جلب أحدث الخاص..."))
    dialogs = await client.get_dialogs(limit=20)
    text = "💬 **أحدث المحادثات الخاصة:**\n"
    count = 0
    for d in dialogs:
        if d.is_user and not d.entity.bot:
            count += 1
            text += f"{count}. {d.name} ➔ (`{d.id}`)\n"
            if count >= 10: break
    await status_msg.edit(text)

# --- م24 ---
@client.on(events.NewMessage(pattern=r"^\.م24(\s+.*)?$"))
async def m24(event):
    if not is_sudo(event): return
    text = f"📌 **صورة البروفايل (`.م24`):**\n• `.صورة البروفايل` (بالرد على صورة)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.صورة البروفايل(\s+.*)?$"))
async def set_profile_photo(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ رد على صورة الأول."
        return await (event.edit(msg) if event.out else event.reply(msg))
    r = await event.get_reply_message()
    if not r.photo:
        msg = "⚠️ دي مش صورة!"
        return await (event.edit(msg) if event.out else event.reply(msg))
    status_msg = await (event.edit("⏳ جاري تغيير صورة بروفايلك...") if event.out else event.reply("⏳ جاري تغيير صورة بروفايلك..."))
    photo = await r.download_media()
    file = await client.upload_file(photo)
    await client(functions.photos.UploadProfilePhotoRequest(file=file))
    if os.path.exists(photo): os.remove(photo)
    await status_msg.edit("🖼 تم تغيير الصورة بنجاح!")

# --- م25 ---
@client.on(events.NewMessage(pattern=r"^\.م25(\s+.*)?$"))
async def m25(event):
    if not is_sudo(event): return
    text = f"📌 **كتم المحادثات الخاصة المباشر (`.م25`):**\n• `.كتمخاص` (في الخاص أو بالرد/باليوزر/بالآيدي)\n• `.فك كتمخاص`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.كتمخاص(?:\s+(.*))?$"))
async def mute_pm(event):
    if not is_sudo(event): return
    target_id = await get_target_user(event)
    if not target_id and event.is_private:
        target_id = event.chat_id

    if not target_id:
        msg = "⚠️ **استخدم الأمر في شات الخاص مباشر أو بالرد أو باليوزر/الآيدي.**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    MUTED_PMS.add(target_id)
    text = f"🔇 **تم كتم الخاص مع الشخص ده:** `{target_id}`"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.فك كتمخاص(?:\s+(.*))?$"))
async def unmute_pm(event):
    if not is_sudo(event): return
    target_id = await get_target_user(event)
    if not target_id and event.is_private:
        target_id = event.chat_id

    if not target_id:
        msg = "⚠️ **استخدم الأمر في شات الخاص مباشر أو بالرد أو باليوزر/الآيدي.**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    if target_id in MUTED_PMS:
        MUTED_PMS.remove(target_id)
        text = f"🔊 **تم فك كتم الخاص مع:** `{target_id}`"
    else:
        text = "⚠️ **الشخص ده مش مكتوم خاص.**"
    await (event.edit(text) if event.out else event.reply(text))

# --- م26 ---
@client.on(events.NewMessage(pattern=r"^\.م26(\s+.*)?$"))
async def m26(event):
    if not is_sudo(event): return
    text = f"📌 **حفظ الميديا والذاتية (`.م26`):**\n• `.حفظ` (بالرد على ميديا عادي)\n• `.حفظ الذاتية` (بالرد على صورة/فيديو ذاتي التدمير)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.حفظ(\s+.*)?$"))
async def save_media_cmd(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ بالرد على الصورة أو الفيديو."
        return await (event.edit(msg) if event.out else event.reply(msg))
    r = await event.get_reply_message()
    if not (r.photo or r.video or r.media):
        msg = "⚠️ مفيش ميديا في الرسالة!"
        return await (event.edit(msg) if event.out else event.reply(msg))
    status_msg = await (event.edit("⏳ جاري التحميل...") if event.out else event.reply("⏳ جاري التحميل..."))
    file_path = await r.download_media()
    await client.send_file("me", file_path, caption=f"📥 **تم الحفظ في المحفوظات.**\n{SOURCE_TITLE}")
    if os.path.exists(file_path): os.remove(file_path)
    await status_msg.edit("✅ **تم الإرسال للرسائل المحفوظة (Saved Messages)!**")

@client.on(events.NewMessage(pattern=r"^\.(حفظ الذاتيه|ذاتيه|حفظ الذاتية)(\s+.*)?$"))
async def save_self_destruct_media(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ **رد على الصورة أو الفيديو ذاتي التدمير!**"
        return await (event.edit(msg) if event.out else event.reply(msg))
    r = await event.get_reply_message()
    if not (r.photo or r.video or r.media):
        msg = "⚠️ **الرسالة المردود عليها مفيهاش ميديا!**"
        return await (event.edit(msg) if event.out else event.reply(msg))
    
    status_msg = await (event.edit("⏳ **جاري تحميل الميديا ذاتية التدمير...**") if event.out else event.reply("⏳ **جاري تحميل الميديا ذاتية التدمير...**"))
    try:
        file_path = await client.download_media(r)
        if file_path:
            await client.send_file("me", file_path, caption=f"📥 **تم حفظ الميديا ذاتية التدمير بنجاح!**\n{SOURCE_TITLE}")
            if os.path.exists(file_path):
                os.remove(file_path)
            await status_msg.edit("✅ **تم حفظ الصورة/الفيديو ذاتي التدمير وحفظها في الرسائل المحفوظة!**")
        else:
            await status_msg.edit("❌ **فشل تحميل الميديا.**")
    except Exception as e:
        await status_msg.edit(f"❌ **حدث خطأ أثناء حفظ الذاتية:** {e}")

# --- م27 ---
@client.on(events.NewMessage(pattern=r"^\.م27(\s+.*)?$"))
async def m27(event):
    if not is_sudo(event): return
    text = f"📌 **معرفة رتب الأعضاء (`.م27`):**\n• `.رتبتي`\n• `.رتبته` (بالرد/باليوزر/بالآيدي)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.رتبتي(\s+.*)?$"))
async def my_rank(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ جوة الجروبات بس."
        return await (event.edit(msg) if event.out else event.reply(msg))
    perms = await client.get_permissions(event.chat_id, event.sender_id)
    if perms.is_creator: rank = "👑 المالك الأساسي"
    elif perms.is_admin: rank = "🛡 أدمن في الجروب"
    else: rank = "👤 عضو عادي"
    text = f"📊 **رتبتك:** {rank}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.رتبته(?:\s+(.*))?$"))
async def user_rank(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ جوة الجروبات بس."
        return await (event.edit(msg) if event.out else event.reply(msg))
        
    target_id = await get_target_user(event)
    if not target_id:
        msg = "⚠️ **حدد العضو بالرد أو باليوزر أو بالآيدي.**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    try:
        perms = await client.get_permissions(event.chat_id, target_id)
        if perms.is_creator: rank = "👑 المالك الأساسي"
        elif perms.is_admin: rank = "🛡 أدمن في الجروب"
        else: rank = "👤 عضو عادي"
        text = f"📊 **رتبة العضو [`{target_id}`]:** {rank}"
    except Exception as e:
        text = f"❌ **تعذر معرفة الرتبة:** `{e}`"
    await (event.edit(text) if event.out else event.reply(text))

# --- م28 ---
@client.on(events.NewMessage(pattern=r"^\.م28(\s+.*)?$"))
async def m28(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر النظام (`.م28`):**\n• `.ريستارت`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.ريستارت(\s+.*)?$"))
async def restart_script(event):
    if not is_sudo(event): return
    await (event.edit("🔄 **جاري إعادة تشغيل السورس...**") if event.out else event.reply("🔄 **جاري إعادة تشغيل السورس...**"))
    os.execl(sys.executable, sys.executable, *sys.argv)

# ----------------------------------------------------
# 10. معالج الرسائل القادمة لتطبيق الحظر والتنفيذ التلقائي
# ----------------------------------------------------
@client.on(events.NewMessage)
async def handle_incoming(event):
    if not event.sender_id or event.sender_id in TELEGRAM_SYSTEM_IDS:
        return

    global SLEEP_ACTIVE
    if event.out and SLEEP_ACTIVE:
        SLEEP_ACTIVE = False

    # فحص الحظر العام GBAN
    if event.sender_id in GBAN_SET and not event.out:
        try:
            await client(EditBannedRequest(event.chat_id, event.sender_id, ChatBannedRights(until_date=None, view_messages=True)))
            await event.delete()
        except Exception:
            pass
        return

    # فحص الكتم العام GMUTE
    if event.sender_id in GMUTE_SET and not event.out:
        try:
            await event.delete()
        except Exception:
            pass
        return

    # فحص كتم الجروب MUTED_USERS
    if event.is_group and event.chat_id in MUTED_USERS:
        if event.sender_id in MUTED_USERS[event.chat_id] and not event.out:
            try:
                await event.delete()
            except Exception:
                pass
            return

    # فحص كتم الخاص MUTED_PMS
    if event.is_private and event.chat_id in MUTED_PMS and not event.out:
        try:
            await event.delete()
        except Exception:
            pass
        return

    # حفظ صور الفيديو والخاص الذاتية تلقائياً
    if AUTO_SAVE_MEDIA and event.is_private and not event.out:
        if event.photo or event.video or event.media:
            try:
                file_path = await client.download_media(event.media)
                if file_path:
                    await client.send_file("me", file_path, caption=f"📥 **حفظ تلقائي للميديا من:** `{event.sender_id}`\n{SOURCE_TITLE}")
                    if os.path.exists(file_path):
                        os.remove(file_path)
            except Exception:
                pass

    # حماية الخاص PM Guard
    if PM_PROTECTION_ACTIVE and event.is_private and not event.out and not is_sudo(event):
        if event.sender_id not in APPROVED_USERS:
            count = PM_WARNINGS.get(event.sender_id, 0) + 1
            PM_WARNINGS[event.sender_id] = count
            if count >= 7:
                await event.reply("⛔ **تم حظرك تلقائياً لتجاوز عدد التحذيرات المسموح بها.**")
                await client(BlockRequest(id=event.sender_id))
            else:
                await event.reply(f"*!**\nبلاش سبام عشان متاخدش بان تلقائي.\n⚠️ تحذير `{count}/7`")

    # الردود التلقائية
    if event.text in REPLY_MAP and not event.out:
        await event.reply(REPLY_MAP[event.text])

    # الكلمات الممنوعة
    if BLOCKED_WORDS and not event.out and event.text:
        for word in BLOCKED_WORDS:
            if word in event.text:
                try:
                    await event.delete()
                except Exception:
                    pass
                break

# ----------------------------------------------------
# 11. تشغيل الحساب
# ----------------------------------------------------
print("⚡ Portuguese source client started successfully...")
client.start()
client.run_until_disconnected()

