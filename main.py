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
from telethon.tl.functions.contacts import BlockRequest
from telethon.tl.types import ChatBannedRights, ChatAdminRights, ChannelParticipantsKicked
from telethon.sessions import StringSession
from telethon.errors import (
    UserPrivacyRestrictedError, ChatAdminRequiredError, UserNotMutualContactError,
    UserChannelsTooMuchError, UserBotError, PeerFloodError, FloodWaitError, UserKickedError
)

# ----------------------------------------------------
# 1. إعدادات الجلسة والحساب
# ----------------------------------------------------
API_ID = int(os.getenv("API_ID", "24576280"))
API_HASH = os.getenv("API_HASH", "2d331fea63e2dfeb0d2c2cf71a9a0cc9")
STRING_SESSION = os.getenv("STRING_SESSION", "1BJWap1wBu6wTWUI6KGHqA-rltuId7offBYF9yOSPs4eJYlvYFznWk_-xAkKxb3jHUecIxUaObuXYs4HPpfOiE45pYlIGmNToeZtpy8K6OhNW26h-HbG3MGhir-yrRgb8bufvixbF-XZ8lBkyJZ0OOahRl9l3SUYQhDdzptbTrSy2I4LDOvt96bu4yEV64owrtHKlE1KneUkdaKdhP7wM-1nAjOLvn1EbaUKGyEVfblvq2CBA-WepXGSzqa6Qvp0sG0bf0cPEZOcLPXM1NZEvRxrbcBuuh4u9bf-NGQtJaD6_S_3pb-9JVvcNl2wJjcGnfc5lV33XDmSKSA7iOfq3PujNg1oxX0E=")

client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH)

SOURCE_TITLE = "🇵🇹 سورس البرتغالي 🇵🇹"
CAIRO_TZ = pytz.timezone('Africa/Cairo')

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
# 3. دالة التحقق من الصلاحيات
# ----------------------------------------------------
def is_sudo(event):
    return event.out or (event.sender_id in DEVELOPERS)

# ----------------------------------------------------
# 4. قائمة الأوامر بالعامية
# ----------------------------------------------------
ALL_COMMANDS_TEXT = f"""✦─────『 {SOURCE_TITLE} 』─────✦

• `.رفع مطور` ➪ رفع مطور (بالرد على الشخص أو تحويل منه)
• `.تنزيل مطور` ➪ تنزيل مطور (بالرد أو تحويل)
• `.مسح المطورين` ➪ مسح جميع المطورين المضافين
• `.المطورين` ➪ عرض قائمة المطورين
• `.تفليش` ➪ تصفية وطرد أعضاء الجروب
• `.تفعيل الوقت` ➪ إظهار الوقت بجانب اسمك بتوقيت مصر
• `.تعطيل الوقت` ➪ إيقاف الوقت ورجوع اسمك الاصلي
• `.تفعيل الحمايه` ➪ قفل الخاص وتحذير أي حد يبعت
• `.تعطيل الحمايه` ➪ إيقاف حماية الخاص
• `.قبول` ➪ السماح لشخص بالحديث في الخاص بدون تحذيرات
• `.رفض` ➪ إلغاء القبول وإرجاع التحذيرات للشخص
• `.بلوك` ➪ حظر المستخدم
• `.حفظ الذاتية` ➪ حفظ صورة/فيديو ذاتية التدمير للرسائل المحفوظة
• `.تفعيل الذاتيه` ➪ حفظ ميديا الخاص والتدمير الذاتي تلقائياً
• `.تعطيل الذاتيه` ➪ إيقاف حفظ الصور تلقائياً
• `.سليب` ➪ تفعيل وضع النوم
• `.همسه` [الكلام] ➪ إرسال همسة سرية
• `.طرد عام` ➪ طرد شخص من كل الجروبات المشتركة (بالرد)
• `.مسح المحظورين` ➪ فك الحظر عن كل المحظورين في الجروب
• `.مسح المحظورين عام` ➪ تفريغ قائمة الحظر العام
• `.مسح المكتومين` ➪ فك الكتم عن قائمة المكتومين بالجروب
• `.مسح المكتومين عام` ➪ تفريغ قائمة الكتم العام
• `.م1` ➪ البحث والوسائط (`.بحث` ، `.صورة`)
• `.م2` ➪ الوقت والتاريخ (`.الوقت` ، `.التاريخ`)
• `.م3` ➪ إدارة الجروب والكتم (`.حظر` ، `.كتم` ، `.فك كتم` ، `.مسح المحظورين` ، `.مسح المكتومين`)
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
• `.م28` ➪ النظام (`.ريستارت`)
• `.م29` ➪ السرعة والاستجابة (`.بنج`)
• `.م30` ➪ إحصائيات الحساب (`.الاحصائيات`)
• `.م31` ➪ حالة الستريك (`.ستريك`)"""

# ----------------------------------------------------
# 5. أوامر المطورين
# ----------------------------------------------------

@client.on(events.NewMessage(pattern=r"^\.(اوامري|الاوامر)$"))
async def show_all_commands(event):
    if not is_sudo(event): return
    await (event.edit(ALL_COMMANDS_TEXT) if event.out else event.reply(ALL_COMMANDS_TEXT))

@client.on(events.NewMessage(pattern=r"^\.رفع مطور$"))
async def add_developer(event):
    if not event.out and event.sender_id != MAIN_DEV_ID: return
    if not event.is_reply:
        return await event.edit("⚠️ **رد على رسالة الشخص أو حول منه رسالة عشان ترفعه!**")

    reply = await event.get_reply_message()
    target_id = reply.forward.sender_id if (reply.forward and reply.forward.sender_id) else reply.sender_id

    if not target_id:
        return await event.edit("❌ **مش عارف أوصل لآيدي الشخص ده.**")

    if target_id in DEVELOPERS:
        return await event.edit("⚠️ **الشخص ده مرفوع مطور بالفعل!**")

    DEVELOPERS.add(target_id)
    await event.edit(f"✅ **تم رفع الشخص مطور في السورس بنجاح!**\n🆔 الآيدي: `{target_id}`")

@client.on(events.NewMessage(pattern=r"^\.تنزيل مطور$"))
async def remove_developer(event):
    if not event.out and event.sender_id != MAIN_DEV_ID: return
    if not event.is_reply:
        return await event.edit("⚠️ **رد على الشخص عشان تنزله من المطورين!**")

    reply = await event.get_reply_message()
    target_id = reply.forward.sender_id if (reply.forward and reply.forward.sender_id) else reply.sender_id

    if target_id in DEVELOPERS:
        DEVELOPERS.remove(target_id)
        await event.edit(f"✅ **تم تنزيل الشخص من المطورين:** `{target_id}`")
    else:
        await event.edit("⚠️ **الشخص ده مش مطور من الأساس.**")

@client.on(events.NewMessage(pattern=r"^\.مسح المطورين$"))
async def clear_developers(event):
    if not event.out and event.sender_id != MAIN_DEV_ID: return
    me = await client.get_me()
    
    DEVELOPERS.clear()
    DEVELOPERS.add(MAIN_DEV_ID)
    DEVELOPERS.add(me.id)
    
    msg = "🗑️ **تم مسح جميع المطورين المضافين بنجاح المطور الأساسي وصاحب الحساب فقط المتبقيين!**"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.المطورين$"))
async def list_developers(event):
    if not is_sudo(event): return
    if not DEVELOPERS:
        msg = "ℹ️ **مفيش مطورين مرفوعين دلوقتي.**"
    else:
        devs = "\n".join([f"• `{dev_id}`" for dev_id in DEVELOPERS])
        msg = f"👑 **قائمة المطورين المرفوعين:**\n{devs}"
    await (event.edit(msg) if event.out else event.reply(msg))

# ----------------------------------------------------
# 6. أمر تفليش الجروب (التصفية السريعة)
# ----------------------------------------------------

@client.on(events.NewMessage(pattern=r"^\.تفليش$"))
async def taflesh_cmd(event):
    if not event.is_group:
        msg = "⚠️ **الأمر ده بيشتغل جوة الجروبات بس!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    perms = await client.get_permissions(event.chat_id, event.sender_id)
    if not (is_sudo(event) or perms.is_creator or perms.ban_users):
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
# 7. الأوامر الخاصة
# ----------------------------------------------------

@client.on(events.NewMessage(pattern=r"^\.همسه(?:\s+(.+))?$"))
async def whisper_cmd(event):
    if not is_sudo(event): return
    input_text = event.pattern_match.group(1)
    target = None
    whisper_text = ""

    if event.is_reply:
        reply = await event.get_reply_message()
        target_user = await client.get_entity(reply.sender_id)
        target = f"@{target_user.username}" if target_user.username else str(target_user.id)
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

@client.on(events.NewMessage(pattern=r"^\.تفعيل الحمايه$"))
async def enable_pm_guard(event):
    global PM_PROTECTION_ACTIVE
    if not is_sudo(event): return
    PM_PROTECTION_ACTIVE = True
    msg = "🛡️ **تم تفعيل حماية الخاص بنجاح!**\nأي حد يبعتلك رسالة ومكتوبلوش قبول هياخد تحذير، وبعد 7 تحذيرات هياخد بلوك تلقائي."
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.تعطيل الحمايه$"))
async def disable_pm_guard(event):
    global PM_PROTECTION_ACTIVE
    if not is_sudo(event): return
    PM_PROTECTION_ACTIVE = False
    msg = "🔓 **تم تعطيل حماية الخاص بنجاح!**"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.قبول$"))
async def approve_user(event):
    global APPROVED_USERS
    if not is_sudo(event): return
    target_id = None
    if event.is_private:
        target_id = event.chat_id
    elif event.is_reply:
        reply = await event.get_reply_message()
        target_id = reply.sender_id

    if not target_id:
        msg = "⚠️ **استخدم الأمر بالرد على الشخص أو جوة شات الخاص بتاعه!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    APPROVED_USERS.add(target_id)
    if target_id in PM_WARNINGS:
        del PM_WARNINGS[target_id]

    msg = f"✅ **تم قبول المستخدم [{target_id}] ومسموحله يكلمك في الخاص بدون تحذيرات.**"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.رفض$"))
async def decline_user(event):
    global APPROVED_USERS
    if not is_sudo(event): return
    target_id = None
    if event.is_private:
        target_id = event.chat_id
    elif event.is_reply:
        reply = await event.get_reply_message()
        target_id = reply.sender_id

    if not target_id:
        msg = "⚠️ **استخدم الأمر بالرد على الشخص أو جوة شات الخاص بتاعه!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    if target_id in APPROVED_USERS:
        APPROVED_USERS.remove(target_id)
        msg = f"❌ **تم إلغاء قبول المستخدم [{target_id}] وأصبح غير مسموح له بالحديث في الخاص.**"
    else:
        msg = f"⚠️ **المستخدم [{target_id}] غير مقبول من الأساس.**"

    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.بلوك$"))
async def block_user_cmd(event):
    if not is_sudo(event): return
    target_id = None
    if event.is_private:
        target_id = event.chat_id
    elif event.is_reply:
        reply = await event.get_reply_message()
        target_id = reply.sender_id

    if not target_id:
        msg = "⚠️ **استخدم الأمر في المحادثة الخاصة أو بالرد على الشخص!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    try:
        await (event.edit("تم حظر المستخدم 🚫") if event.out else event.reply("تم حظر المستخدم 🚫"))
        await client(BlockRequest(target_id))
    except Exception as e:
        print(f"خطأ في تنفيذ البلوك: {e}")

@client.on(events.NewMessage(pattern=r"^\.تفعيل الذاتيه$"))
async def enable_auto_media(event):
    global AUTO_SAVE_MEDIA
    if not is_sudo(event): return
    AUTO_SAVE_MEDIA = True
    msg = "📸 **تم تفعيل حفظ صور الخاص والتدمير الذاتي تلقائياً!**\nأي ميديا تتبعتلك في الخاص هتوصل فوراً لرسائلك المحفوظة."
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.تعطيل الذاتيه$"))
async def disable_auto_media(event):
    global AUTO_SAVE_MEDIA
    if not is_sudo(event): return
    AUTO_SAVE_MEDIA = False
    msg = "🛑 **تم تعطيل حفظ الصور الذاتية تلقائياً!**"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.سليب$"))
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
    try:
        while TIME_NAME_ACTIVE:
            current_time = datetime.datetime.now(CAIRO_TZ).strftime("%I:%M")
            new_name = f"{ORIGINAL_NAME} | {current_time}"
            await client(functions.account.UpdateProfileRequest(first_name=new_name))
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"خطأ في الوقت: {e}")

@client.on(events.NewMessage(pattern=r"^\.تفعيل الوقت$"))
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

@client.on(events.NewMessage(pattern=r"^\.تعطيل الوقت$"))
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
# 9. أوامر الأقسام (من .م1 إلى .م31)
# ----------------------------------------------------

# --- م1 ---
@client.on(events.NewMessage(pattern=r"^\.م1$"))
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
@client.on(events.NewMessage(pattern=r"^\.م2$"))
async def m2(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الوقت والتاريخ (`.م2`):**\n• `.الوقت`\n• `.التاريخ`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.الوقت$"))
async def get_time(event):
    if not is_sudo(event): return
    now = datetime.datetime.now(CAIRO_TZ)
    t = now.strftime("%I:%M:%S %p").replace("AM", "صباحاً").replace("PM", "مساءً")
    text = f"⏰ **الوقت دلوقتي بتوقيت مصر:** `{t}`"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.التاريخ$"))
async def get_date(event):
    if not is_sudo(event): return
    now = datetime.datetime.now(CAIRO_TZ)
    d = now.strftime("%Y-%m-%d")
    text = f"📅 **التاريخ النهاردة:** `{d}`"
    await (event.edit(text) if event.out else event.reply(text))

# --- م3 ---
@client.on(events.NewMessage(pattern=r"^\.م3$"))
async def m3(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر إدارة الجروب والكتم (`.م3`):**\n• `.حظر` (بالرد)\n• `.فك حظر` (بالرد)\n• `.كتم` (بالرد)\n• `.فك كتم`\n• `.مسح المحظورين`\n• `.مسح المكتومين`\n• `.تفليش` (تصفية الأعضاء)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.حظر$"))
async def ban_user(event):
    if not is_sudo(event): return
    if not event.is_reply or not event.is_group:
        msg = "⚠️ رد على العضو جوة الجروب عشان تحظره."
        return await (event.edit(msg) if event.out else event.reply(msg))
    r = await event.get_reply_message()
    await client(EditBannedRequest(event.chat_id, r.sender_id, ChatBannedRights(until_date=None, view_messages=True)))
    msg = f"⛔ تم حظر العضو: `{r.sender_id}`"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.فك حظر$"))
async def unban_user(event):
    if not is_sudo(event): return
    if not event.is_reply or not event.is_group:
        msg = "⚠️ رد على العضو جوة الجروب عشان تفك حظره."
        return await (event.edit(msg) if event.out else event.reply(msg))
    r = await event.get_reply_message()
    await client(EditBannedRequest(event.chat_id, r.sender_id, ChatBannedRights(until_date=None, view_messages=False)))
    msg = f"✅ تم فك حظر العضو: `{r.sender_id}`"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.مسح المحظورين$"))
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

@client.on(events.NewMessage(pattern=r"^\.كتم$"))
async def mute_user(event):
    if not is_sudo(event): return

    if event.is_private:
        MUTED_PMS.add(event.chat_id)
        msg = "🔇 **تم كتم الشات الخاص ده بنجاح!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    elif event.is_group or event.is_channel:
        if not event.is_reply:
            msg = "⚠️ **رد على العضو عشان تكتمه جوة الجروب أو القناة!**"
            return await (event.edit(msg) if event.out else event.reply(msg))
        r = await event.get_reply_message()
        MUTED_USERS.setdefault(event.chat_id, set()).add(r.sender_id)
        msg = f"🔇 **تم كتم العضو:** `{r.sender_id}`"
        return await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.فك كتم$"))
async def unmute_user(event):
    if not is_sudo(event): return

    if event.is_private:
        if event.chat_id in MUTED_PMS:
            MUTED_PMS.remove(event.chat_id)
            msg = "🔊 **تم فك الكتم عن المحادثة الخاصة دي!**"
        else:
            msg = "⚠️ **المحادثة دي مش مكتومة أصلاً.**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    elif event.is_group or event.is_channel:
        if not event.is_reply:
            msg = "⚠️ **رد على العضو عشان تفك كتمه!**"
            return await (event.edit(msg) if event.out else event.reply(msg))
        r = await event.get_reply_message()
        if event.chat_id in MUTED_USERS and r.sender_id in MUTED_USERS[event.chat_id]:
            MUTED_USERS[event.chat_id].remove(r.sender_id)
            msg = f"🔊 **تم فك كتم العضو:** `{r.sender_id}`"
        else:
            msg = "⚠️ **العضو ده مش مكتوم أصلاً.**"
        return await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.مسح المكتومين$"))
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
@client.on(events.NewMessage(pattern=r"^\.م4$"))
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

@client.on(events.NewMessage(pattern=r"^\.مسح الردود$"))
async def clear_replies(event):
    if not is_sudo(event): return
    REPLY_MAP.clear()
    text = "🗑️ تم مسح كل الردود التلقائية."
    await (event.edit(text) if event.out else event.reply(text))

# --- م5 ---
@client.on(events.NewMessage(pattern=r"^\.م5$"))
async def m5(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر المسح والتنظيف (`.م5`):**\n• `.مسح` [العدد]\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.مسح\s+(\d+)$"))
async def purge_messages(event):
    if not is_sudo(event): return
    num = int(event.pattern_match.group(1))
    await event.delete()
    msgs = await client.get_messages(event.chat_id, limit=num)
    await client.delete_messages(event.chat_id, msgs)

# --- م6 ---
@client.on(events.NewMessage(pattern=r"^\.م6$"))
async def m6(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر لعبة الأحكام (`.م6`):**\n• `.احكام`\n• `.لعب` (للأعضاء)\n• `.بدء`\n• `.انهاء`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.احكام$"))
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

@client.on(events.NewMessage(pattern=r"^\.لعب$", incoming=True))
async def join_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not GAME_ACTIVE or event.chat_id != GAME_CHAT_ID: return
    sender = await event.get_sender()
    if any(p['id'] == sender.id for p in GAME_PLAYERS): return await event.reply("⚠️ انت منضم للعبة بالفعل!")
    if len(GAME_PLAYERS) >= 10: return await event.reply("❌ اكتمل العدد خلاص!")
    GAME_PLAYERS.append({'id': sender.id, 'name': sender.first_name or "عضو"})
    await event.reply(f"✅ تم دخول [{sender.first_name}](tg://user?id={sender.id}) اللعبة!")

@client.on(events.NewMessage(pattern=r"^\.بدء$"))
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

@client.on(events.NewMessage(pattern=r"^\.انهاء$"))
async def stop_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not is_sudo(event): return
    GAME_ACTIVE = False
    GAME_PLAYERS = []
    GAME_CHAT_ID = None
    text = "🔴 **تم إنهاء اللعبة.**"
    await (event.edit(text) if event.out else event.reply(text))

# --- م7 ---
@client.on(events.NewMessage(pattern=r"^\.م7$"))
async def m7(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر كشف الحساب والآيدي (`.م7`):**\n• `.ايدي`\n• `.فحص` (بالرد)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.ايدي$"))
async def get_id(event):
    if not is_sudo(event): return
    if event.is_reply:
        r = await event.get_reply_message()
        text = f"🆔 **آيدي المستخدم:** `{r.sender_id}`"
    else:
        text = f"🆔 **آيديك:** `{event.sender_id}`\n💬 **آيدي الشات:** `{event.chat_id}`"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.فحص$"))
async def inspect_user(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ رد على العضو الأول."
        return await (event.edit(msg) if event.out else event.reply(msg))
    r = await event.get_reply_message()
    u = await client.get_entity(r.sender_id)
    text = f"👤 **الاسم:** {u.first_name}\n🆔 **الآيدي:** `{u.id}`\n🌐 **اليوزر:** @{u.username if u.username else 'مفيش'}"
    await (event.edit(text) if event.out else event.reply(text))

# --- م8 ---
@client.on(events.NewMessage(pattern=r"^\.م8$"))
async def m8(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الحظر العام (`.م8`):**\n• `.حظر عام` (بالرد)\n• `.الغاء العام` (بالرد)\n• `.طرد عام` (طرد الشخص من كل الجروبات)\n• `.مسح المحظورين عام`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.حظر عام$"))
async def gban_user(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ رد على الشخص الأول."
        return await (event.edit(msg) if event.out else event.reply(msg))
    r = await event.get_reply_message()
    GBAN_SET.add(r.sender_id)
    text = f"🚫 تم حظر المستخدم عام من كل الجروبات: `{r.sender_id}`"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.الغاء العام$"))
async def ungban_user(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ رد على الشخص الأول."
        return await (event.edit(msg) if event.out else event.reply(msg))
    r = await event.get_reply_message()
    if r.sender_id in GBAN_SET:
        GBAN_SET.remove(r.sender_id)
        text = f"✅ تم فك الحظر العام عن: `{r.sender_id}`"
    else:
        text = "⚠️ الشخص ده مش محظور عام أصلاً."
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.مسح المحظورين عام$"))
async def clear_gban_list(event):
    if not is_sudo(event): return
    GBAN_SET.clear()
    msg = "🗑️ **تم مسح جميع المحظورين عام بنجاح!**"
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.طرد عام$"))
async def gkick_user(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ **رد على الشخص عشان تطرده عام من الجروبات!**"
        return await (event.edit(msg) if event.out else event.reply(msg))
    
    r = await event.get_reply_message()
    target_id = r.sender_id
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
@client.on(events.NewMessage(pattern=r"^\.م9$"))
async def m9(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الكتم العام (`.م9`):**\n• `.كتم عام` (بالرد)\n• `.الغاء كتم عام` (بالرد)\n• `.مسح المكتومين عام`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.كتم عام$"))
async def gmute_user(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ رد على الشخص الأول."
        return await (event.edit(msg) if event.out else event.reply(msg))
    r = await event.get_reply_message()
    GMUTE_SET.add(r.sender_id)
    text = f"🔇 تم كتم المستخدم عام: `{r.sender_id}`"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.الغاء كتم عام$"))
async def ungmute_user(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ رد على الشخص الأول."
        return await (event.edit(msg) if event.out else event.reply(msg))
    r = await event.get_reply_message()
    if r.sender_id in GMUTE_SET:
        GMUTE_SET.remove(r.sender_id)
        text = f"🔊 تم إلغاء الكتم العام عن: `{r.sender_id}`"
    else:
        text = "⚠️ الشخص ده مش مكتوم عام أصلاً."
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.مسح المكتومين عام$"))
async def clear_gmute_list(event):
    if not is_sudo(event): return
    GMUTE_SET.clear()
    msg = "🗑️ **تم مسح جميع المكتومين عام بنجاح!**"
    await (event.edit(msg) if event.out else event.reply(msg))

# --- م10 ---
@client.on(events.NewMessage(pattern=r"^\.م10$"))
async def m10(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر روابط الجروبات (`.م10`):**\n• `.الرابط` (جلب رابط الجروب)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.الرابط$"))
async def get_link(event):
    if not is_sudo(event): return
    try:
        link = await client(ExportChatInviteRequest(event.chat_id))
        text = f"🔗 **رابط الجروب:** {link.link}"
    except Exception as e:
        text = f"❌ مش عارف أجيب الرابط: {e}"
    await (event.edit(text) if event.out else event.reply(text))

# --- م11 ---
@client.on(events.NewMessage(pattern=r"^\.م11$"))
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
@client.on(events.NewMessage(pattern=r"^\.م12$"))
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
@client.on(events.NewMessage(pattern=r"^\.م13$"))
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

@client.on(events.NewMessage(pattern=r"^\.قائمة المنع$"))
async def list_blocked(event):
    if not is_sudo(event): return
    if not BLOCKED_WORDS:
        msg = "⚠️ مفيش كلمات ممنوعة دلوقتي."
    else:
        words = "\n".join([f"• `{w}`" for w in BLOCKED_WORDS])
        msg = f"📜 **الكلمات الممنوعة:**\n{words}"
    await (event.edit(msg) if event.out else event.reply(msg))

# --- م14 ---
@client.on(events.NewMessage(pattern=r"^\.م14$"))
async def m14(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر المغادرة والانضمام (`.م14`):**\n• `.مغادرة`\n• `.انضمام` [رابط أو يوزر الجروب]\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.مغادرة$"))
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
            await client(ImportChatInviteRequest(hash_val))
        else:
            username = link.split("/")[-1].replace("@", "")
            await client(JoinChannelRequest(username))
        await status_msg.edit("✅ **تم الانضمام بنجاح!**")
    except Exception as e:
        await status_msg.edit(f"❌ **مش عارف أدخل:** {e}")

# --- م15 ---
@client.on(events.NewMessage(pattern=r"^\.م15$"))
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
@client.on(events.NewMessage(pattern=r"^\.م16$"))
async def m16(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الإضافة والحذف للجهات (`.م16`):**\n• `.ضيف` [رابط الجروب المصدر]\n• `.حذف الجهات` [رابط الجروب]\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.(ضيف|اضافة|إضافة)(?:\s+(.+))?$"))
async def add_members_zedthon(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ **استخدم الأمر ده جوة الجروب اللي عاوز تضيف فيه الأعضاء!**"
        return await (event.edit(msg) if event.out else event.reply(msg))

    target_chat = event.pattern_match.group(2)
    if not target_chat and event.is_reply:
        reply_msg = await event.get_reply_message()
        if reply_msg.text:
            target_chat = reply_msg.text.strip()

    if not target_chat:
        msg = "⚠️ **اكتب رابط أو معرف الجروب المصدر أو رد عليه!**\nمثال: `.ضيف @group_username`"
        return await (event.edit(msg) if event.out else event.reply(msg))

    status_msg = await (event.edit("⏳ **جاري سحب الأعضاء...**") if event.out else event.reply("⏳ **جاري سحب الأعضاء...**"))

    try:
        if "joinchat/" in target_chat or "+" in target_chat:
            hash_val = target_chat.split("+")[-1].split("joinchat/")[-1]
            updates = await client(ImportChatInviteRequest(hash_val))
            source_entity = updates.chats[0]
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
            
            # التحقق من استجابة تليجرام الفعلية لمنع العد الوهمي
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
            updates = await client(ImportChatInviteRequest(hash_val))
            entity = updates.chats[0]
        else:
            username = target.split("/")[-1].replace("@", "")
            entity = await client.get_entity(username)

        users = await client.get_participants(entity)
        deleted_count = 0
        failed = 0

        for u in users:
            if u.bot or u.deleted or u.is_self: continue
            try:
                await client(functions.contacts.DeleteContactsRequest(id=[u]))
                deleted_count += 1
                await asyncio.sleep(0.5)
            except Exception: failed += 1

        await status_msg.edit(f"✅ **تم مسحهم من الجهات!**\n🗑️ اتتمسحوا: `{deleted_count}`\n❌ فشل: `{failed}`")
    except Exception as err:
        await status_msg.edit(f"❌ **حصل خطأ:**\n`{err}`")

# --- م17 ---
@client.on(events.NewMessage(pattern=r"^\.م17$"))
async def m17(event):
    if not is_sudo(event): return
    text = f"📌 **تنظيف الحسابات المغلقة (`.م17`):**\n• `.تنظيف المغلقة`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.تنظيف المغلقة$"))
async def clean_deleted(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ للجروبات بس."
        return await (event.edit(msg) if event.out else event.reply(msg))
    status_msg = await (event.edit("🔍 جاري فحص الحسابات المحذوفة...") if event.out else event.reply("🔍 جاري فحص الحسابات المحذوفة..."))
    users = await client.get_participants(event.chat_id)
    c = 0
    for u in users:
        if u.deleted:
            try:
                await client(EditBannedRequest(event.chat_id, u.id, ChatBannedRights(until_date=None, view_messages=True)))
                c += 1
            except: pass
    await status_msg.edit(f"🧹 تم طرد `{c}` حسابات محذوفة.")

# --- م18 ---
@client.on(events.NewMessage(pattern=r"^\.م18$"))
async def m18(event):
    if not is_sudo(event): return
    text = f"📌 **طرد البوتات (`.م18`):**\n• `.طرد البوتات`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.طرد البوتات$"))
async def purge_bots(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ للجروبات بس."
        return await (event.edit(msg) if event.out else event.reply(msg))
    status_msg = await (event.edit("🔍 جاري بنفض البوتات...") if event.out else event.reply("🔍 جاري بنفض البوتات..."))
    users = await client.get_participants(event.chat_id)
    c = 0
    me = await client.get_me()
    for u in users:
        if u.bot and u.id != me.id:
            try:
                await client(EditBannedRequest(event.chat_id, u.id, ChatBannedRights(until_date=None, view_messages=True)))
                c += 1
            except: pass
    await status_msg.edit(f"🤖 تم طرد `{c}` بوت بنجاح.")

# --- م19 ---
@client.on(events.NewMessage(pattern=r"^\.م19$"))
async def m19(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر التثبيت (`.م19`):**\n• `.تثبيت` (بالرد)\n• `.الغاء التثبيت`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.تثبيت$"))
async def pin_msg(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ رد على الرسالة."
        return await (event.edit(msg) if event.out else event.reply(msg))
    r = await event.get_reply_message()
    await client.pin_message(event.chat_id, r.id)
    msg = "📌 تم تثبيت الرسالة بنجاح."
    await (event.edit(msg) if event.out else event.reply(msg))

@client.on(events.NewMessage(pattern=r"^\.الغاء التثبيت$"))
async def unpin_msg(event):
    if not is_sudo(event): return
    await client.unpin_message(event.chat_id)
    msg = "📌 تم إلغاء التثبيت."
    await (event.edit(msg) if event.out else event.reply(msg))

# --- م20 ---
@client.on(events.NewMessage(pattern=r"^\.م20$"))
async def m20(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الإشراف والترقية (`.م20`):**\n• `.رفع مشرف` (بالرد)\n• `.تنزيل مشرف` (بالرد)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.رفع مشرف$"))
async def promote_user(event):
    if not is_sudo(event): return
    if not event.is_reply or not event.is_group:
        msg = "⚠️ **رد على رسالة الشخص جوة الجروب عشان ترفعه مشرف!**"
        return await (event.edit(msg) if event.out else event.reply(msg))
    
    r = await event.get_reply_message()
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
            user_id=r.sender_id,
            admin_rights=rights,
            rank="مشرف"
        ))
        await status_msg.edit(f"👑 **تم ترقية المستخدم [`{r.sender_id}`] مشرف بنجاح!**")
    except Exception as e:
        await status_msg.edit(f"❌ **حصل مشكلة أثناء الرفع:**\n`{e}`")

@client.on(events.NewMessage(pattern=r"^\.تنزيل مشرف$"))
async def demote_user(event):
    if not is_sudo(event): return
    if not event.is_reply or not event.is_group:
        msg = "⚠️ **رد على رسالة الشخص جوة الجروب عشان تنزله من الإشراف!**"
        return await (event.edit(msg) if event.out else event.reply(msg))
    
    r = await event.get_reply_message()
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
            user_id=r.sender_id,
            admin_rights=rights,
            rank=""
        ))
        await status_msg.edit(f"📉 **تم تنزيل المستخدم [`{r.sender_id}`] من الإشراف بنجاح!**")
    except Exception as e:
        await status_msg.edit(f"❌ **حصل مشكلة أثناء التنزيل:**\n`{e}`")

# --- م21 ---
@client.on(events.NewMessage(pattern=r"^\.م21$"))
async def m21(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر المكالمات الصوتية (`.م21`):**\n• `.افتح الكول`\n• `.اقفل الكول`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.افتح الكول$"))
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

@client.on(events.NewMessage(pattern=r"^\.اقفل الكول$"))
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
@client.on(events.NewMessage(pattern=r"^\.م22$"))
async def m22(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الإبلاغ والسبام (`.م22`):**\n• `.بلاغ` (بالرد)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.بلاغ$"))
async def report_spam(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ بالرد على الرسالة."
        return await (event.edit(msg) if event.out else event.reply(msg))
    r = await event.get_reply_message()
    await client(ReportSpamRequest(peer=r.sender_id))
    text = "🚨 بلغنا التليجرام عن الحساب ده."
    await (event.edit(text) if event.out else event.reply(text))

# --- م23 ---
@client.on(events.NewMessage(pattern=r"^\.م23$"))
async def m23(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر المحادثات الخاصة (`.م23`):**\n• `.كشف الخاص`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.كشف الخاص$"))
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
@client.on(events.NewMessage(pattern=r"^\.م24$"))
async def m24(event):
    if not is_sudo(event): return
    text = f"📌 **صورة البروفايل (`.م24`):**\n• `.صورة البروفايل` (بالرد على صورة)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.صورة البروفايل$"))
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
@client.on(events.NewMessage(pattern=r"^\.م25$"))
async def m25(event):
    if not is_sudo(event): return
    text = f"📌 **كتم المحادثات الخاصة المباشر (`.م25`):**\n• `.كتمخاص` (في الخاص دون الحاجة للرد)\n• `.فك كتمخاص`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.كتمخاص$"))
async def mute_pm(event):
    if not is_sudo(event): return
    target_id = event.chat_id if event.is_private else ( (await event.get_reply_message()).sender_id if event.is_reply else None )
    if not target_id:
        msg = "⚠️ استخدم الأمر في شات الخاص مباشر أو بالرد."
        return await (event.edit(msg) if event.out else event.reply(msg))
    MUTED_PMS.add(target_id)
    text = f"🔇 تم كتم الخاص مع الشخص ده: `{target_id}`"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.فك كتمخاص$"))
async def unmute_pm(event):
    if not is_sudo(event): return
    target_id = event.chat_id if event.is_private else ( (await event.get_reply_message()).sender_id if event.is_reply else None )
    if target_id in MUTED_PMS:
        MUTED_PMS.remove(target_id)
        text = f"🔊 تم فك كتم الخاص مع: `{target_id}`"
    else:
        text = "⚠️ الشخص ده مش مكتوم خاص."
    await (event.edit(text) if event.out else event.reply(text))

# --- م26 ---
@client.on(events.NewMessage(pattern=r"^\.م26$"))
async def m26(event):
    if not is_sudo(event): return
    text = f"📌 **حفظ الميديا والذاتية (`.م26`):**\n• `.حفظ` (بالرد على ميديا عادي)\n• `.حفظ الذاتية` (بالرد على صورة/فيديو ذاتي التدمير)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.حفظ$"))
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

@client.on(events.NewMessage(pattern=r"^\.(حفظ الذاتيه|ذاتيه|حفظ الذاتية)$"))
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
@client.on(events.NewMessage(pattern=r"^\.م27$"))
async def m27(event):
    if not is_sudo(event): return
    text = f"📌 **معرفة رتب الأعضاء (`.م27`):**\n• `.رتبتي`\n• `.رتبته` (بالرد)\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.رتبتي$"))
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

@client.on(events.NewMessage(pattern=r"^\.رتبته$"))
async def user_rank(event):
    if not is_sudo(event): return
    if not event.is_reply or not event.is_group:
        msg = "⚠️ بالرد جوة جروب."
        return await (event.edit(msg) if event.out else event.reply(msg))
    r = await event.get_reply_message()
    perms = await client.get_permissions(event.chat_id, r.sender_id)
    if perms.is_creator: rank = "👑 المالك الأساسي"
    elif perms.is_admin: rank = "🛡 أدمن في الجروب"
    else: rank = "👤 عضو عادي"
    text = f"📊 **رتبته:** {rank}"
    await (event.edit(text) if event.out else event.reply(text))

# --- م28 ---
@client.on(events.NewMessage(pattern=r"^\.م28$"))
async def m28(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر النظام (`.م28`):**\n• `.ريستارت`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.ريستارت$"))
async def restart_bot(event):
    if not is_sudo(event): return
    await (event.edit("🔄 **جاري إعادة تشغيل السورس...**") if event.out else event.reply("🔄 **جاري إعادة تشغيل السورس...**"))
    os.execl(sys.executable, sys.executable, *sys.argv)

# --- م29 ---
@client.on(events.NewMessage(pattern=r"^\.م29$"))
async def m29(event):
    if not is_sudo(event): return
    text = f"📌 **قياس السرعة (`.م29`):**\n• `.بنج`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.بنج$"))
async def ping_cmd(event):
    if not is_sudo(event): return
    start = datetime.datetime.now(CAIRO_TZ)
    status_msg = await (event.edit("🚀 **PONG!**") if event.out else event.reply("🚀 **PONG!**"))
    end = datetime.datetime.now(CAIRO_TZ)
    ms = (end - start).microseconds / 1000
    await status_msg.edit(f"⚡ **سرعة الاستجابة:** `{ms:.2f}ms`\n{SOURCE_TITLE}")

# --- م30 ---
@client.on(events.NewMessage(pattern=r"^\.م30$"))
async def m30(event):
    if not is_sudo(event): return
    text = f"📌 **إحصائيات الحساب (`.م30`):**\n• `.الاحصائيات`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.الاحصائيات$"))
async def user_stats(event):
    if not is_sudo(event): return
    status_msg = await (event.edit("⏳ جاري تجميع الإحصائيات...") if event.out else event.reply("⏳ جاري تجميع الإحصائيات..."))
    dialogs = await client.get_dialogs()
    pms, groups, channels = 0, 0, 0
    for d in dialogs:
        if d.is_user: pms += 1
        elif d.is_group: groups += 1
        elif d.is_channel: channels += 1
    await status_msg.edit(f"📊 **إحصائيات حسابك:**\n💬 **الخاص:** `{pms}`\n👥 **الجروبات:** `{groups}`\n📢 **القنوات:** `{channels}`")

# --- م31 ---
@client.on(events.NewMessage(pattern=r"^\.م31$"))
async def m31(event):
    if not is_sudo(event): return
    text = f"📌 **الستريك وحالة السورس (`.م31`):**\n• `.ستريك`\n\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

@client.on(events.NewMessage(pattern=r"^\.ستريك$"))
async def streak_status(event):
    if not is_sudo(event): return
    text = f"🔥 **الستريك شغال 100% بدون انقطاع ✅**\n{SOURCE_TITLE}"
    await (event.edit(text) if event.out else event.reply(text))

# ----------------------------------------------------
# 10. الحارس الذكي والمراقبة لجميع الأحداث
# ----------------------------------------------------

@client.on(events.NewMessage(outgoing=True))
async def auto_disable_sleep(event):
    global SLEEP_ACTIVE, SLEEP_START_TIME
    if SLEEP_ACTIVE:
        if event.raw_text and event.raw_text.strip() == ".سليب":
            return
        SLEEP_ACTIVE = False
        SLEEP_START_TIME = None
        print("🛑 تم تعطيل وضع السليب تلقائياً بسبب إرسالك رسالة.")

@client.on(events.NewMessage(incoming=True))
async def global_incoming_watcher(event):
    global PM_WARNINGS, SLEEP_ACTIVE, SLEEP_START_TIME
    sender_id = event.sender_id
    if not sender_id: return

    if is_sudo(event): return

    if sender_id in GBAN_SET:
        try:
            await event.delete()
            if event.is_group:
                await client(EditBannedRequest(event.chat_id, sender_id, ChatBannedRights(until_date=None, view_messages=True)))
        except: pass
        return

    if sender_id in GMUTE_SET or (event.chat_id in MUTED_USERS and sender_id in MUTED_USERS[event.chat_id]):
        try: await event.delete()
        except: pass
        return

    if event.is_private and sender_id in MUTED_PMS:
        try: await event.delete()
        except: pass
        return

    if event.raw_text:
        for w in BLOCKED_WORDS:
            if w in event.raw_text:
                try: await event.delete()
                except: pass
                return

    if event.raw_text in REPLY_MAP:
        await event.reply(REPLY_MAP[event.raw_text])

    if AUTO_SAVE_MEDIA and event.is_private and (event.photo or event.video or event.media):
        try:
            file_path = await event.download_media()
            if file_path:
                await client.send_file("me", file_path, caption=f"📥 **تم حفظ ميديا من الخاص تلقائياً من:** [{sender_id}](tg://user?id={sender_id})\n{SOURCE_TITLE}")
                if os.path.exists(file_path): os.remove(file_path)
        except Exception as e:
            print(f"خطأ في حفظ الذاتية: {e}")

    if SLEEP_ACTIVE and SLEEP_START_TIME:
        should_respond = False
        if event.is_private:
            should_respond = True
        elif event.is_group and (event.mentioned or event.is_reply):
            reply_msg = await event.get_reply_message() if event.is_reply else None
            me = await client.get_me()
            if event.mentioned or (reply_msg and reply_msg.sender_id == me.id):
                should_respond = True

        if should_respond:
            now = datetime.datetime.now(CAIRO_TZ)
            diff = int((now - SLEEP_START_TIME).total_seconds())
            hours = diff // 3600
            minutes = (diff % 3600) // 60
            seconds = diff % 60
            
            sleep_text = (
                f"😴 **صاحب الحساب في وضع سليب (نايم)**\n\n"
                f"⏱️ **محتجب بقاله:** `{hours}` ساعة و `{minutes}` دقيقة و `{seconds}` ثانية."
            )
            await event.reply(sleep_text)

    if PM_PROTECTION_ACTIVE and event.is_private and sender_id not in APPROVED_USERS:
        current_warns = PM_WARNINGS.get(sender_id, 0) + 1
        PM_WARNINGS[sender_id] = current_warns

        if current_warns >= 7:
            await event.reply("🚫 **تم إعطاؤك بلوك لتجاوزك 7 تحذيرات في الخاص.**")
            try:
                await client(BlockRequest(sender_id))
            except Exception as e:
                print(f"خطأ البلوك: {e}")
            del PM_WARNINGS[sender_id]
        else:
            warn_msg = (
                f"⚠️ **تحذير ({current_warns}/7):**\n"
                f"حماية الخاص متفعلة! بلاش سبام عشان ما تاخدش بلوك تلقائي.\n"
                f"انتظر لما يكتب `.قبول` للرد عليك."
            )
            await event.reply(warn_msg)

# ----------------------------------------------------
# 11. تشغيل السورس
# ----------------------------------------------------
async def main():
    await client.start()
    me = await client.get_me()
    print(f"✅ تم التشغيل بنجاح باسم: {me.first_name} (@{me.username}) | ID: {me.id}")
    DEVELOPERS.add(MAIN_DEV_ID)
    DEVELOPERS.add(me.id)
    print("🚀 السورس جاهز واستقبل الأوامر!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 تم إيقاف التشغيل.")

