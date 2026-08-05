import os
import sys
import asyncio
import datetime
import random
import re
from telethon import TelegramClient, events, functions, types
from telethon.tl.functions.channels import (
    EditBannedRequest, InviteToChannelRequest, GetParticipantsRequest,
    LeaveChannelRequest, CreateChannelRequest, JoinChannelRequest, EditAdminRequest
)
from telethon.tl.functions.messages import (
    DeleteMessagesRequest, ExportChatInviteRequest, ImportChatInviteRequest,
    ReportSpamRequest
)
from telethon.tl.types import ChatBannedRights, ChatAdminRights
from telethon.sessions import StringSession
from telethon.errors import UserPrivacyRestrictedError, ChatAdminRequiredError

# ----------------------------------------------------
# 1. إعدادات الجلسة والحساب
# ----------------------------------------------------
API_ID = 24576280
API_HASH = "2d331fea63e2dfeb0d2c2cf71a9a0cc9"
STRING_SESSION = os.getenv("STRING_SESSION", "1BJWap1wBu6wTWUI6KGHqA-rltuId7offBYF9yOSPs4eJYlvYFznWk_-xAkKxb3jHUecIxUaObuXYs4HPpfOiE45pYlIGmNToeZtpy8K6OhNW26h-HbG3MGhir-yrRgb8bufvixbF-XZ8lBkyJZ0OOahRl9l3SUYQhDdzptbTrSy2I4LDOvt96bu4yEV64owrtHKlE1KneUkdaKdhP7wM-1nAjOLvn1EbaUKGyEVfblvq2CBA-WepXGSzqa6Qvp0sG0bf0cPEZOcLPXM1NZEvRxrbcBuuh4u9bf-NGQtJaD6_S_3pb-9JVvcNl2wJjcGnfc5lV33XDmSKSA7iOfq3PujNg1oxX0E=")

client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH)

SOURCE_TITLE = "🇵🇹 سورس البرتغالي 🇵🇹"

# ----------------------------------------------------
# 2. الذاكرة والمصفوفات
# ----------------------------------------------------
GBAN_SET = set()
GMUTE_SET = set()
MUTED_USERS = {}
MUTED_PMS = set()
REPLY_MAP = {}
BLOCKED_WORDS = set()
DEVELOPERS = set()  # مصفوفة المطورين المرفوعين

GAME_ACTIVE = False
GAME_PLAYERS = []
GAME_CHAT_ID = None

# ----------------------------------------------------
# 3. دالة التحقق من الصلاحيات (صاحب الحساب أو مطور)
# ----------------------------------------------------
def is_sudo(event):
    return event.out or (event.sender_id in DEVELOPERS)

# ----------------------------------------------------
# 4. قائمة الأوامر الكاملة
# ----------------------------------------------------
ALL_COMMANDS_TEXT = f"""✦─────『 {SOURCE_TITLE} 』─────✦

• `.رفع مطور` ➪ رفع مطور (بالرد على الشخص أو على تحويل منه)
• `.تنزيل مطور` ➪ تنزيل مطور (بالرد أو تحويل)
• `.المطورين` ➪ عرض قائمة المطورين
• `.م1` ➪ البحث والوسائط (`.بحث` ، `.صورة`)
• `.م2` ➪ الوقت والتاريخ (`.الوقت` ، `.التاريخ`)
• `.م3` ➪ إدارة الكروب (`.حظر` ، `.فك حظر` ، `.كتم` ، `.فك كتم`)
• `.م4` ➪ الردود (`.رد [كلمة] = [رد]` ، `.مسح الردود`)
• `.م5` ➪ التصفية (`.مسح [عدد]`)
• `.م6` ➪ لعبة الأحكام (`.احكام` ، `.لعب` ، `.بدء` ، `.انهاء`)
• `.م7` ➪ الحساب والآيدي (`.ايدي` ، `.فحص`)
• `.م8` ➪ الحظر العام (`.حظر عام` ، `.الغاء العام`)
• `.م9` ➪ الكتم العام (`.كتم عام` ، `.الغاء كتم عام`)
• `.م10` ➪ روابط المحادثة (`.الرابط`)
• `.م11` ➪ تغيير الاسم (`.اسم [الاسم]`)
• `.م12` ➪ البايو والوصف (`.بايو [الوصف]`)
• `.م13` ➪ حظر الكلمات (`.منع [كلمة]` ، `.قائمة المنع`)
• `.م14` ➪ التحكم بالمجموعات (`.مغادرة` ، `.انضمام [رابط]`)
• `.م15` ➪ إنشاء المجموعات (`.انشاء كروب [الاسم]`)
• `.م16` ➪ الإضافة والحذف (`.ضيف [رابط]` ، `.حذف الجهات [رابط]`)
• `.م17` ➪ الحسابات المحذوفة (`.تنظيف المغلقة`)
• `.م18` ➪ إدارة البوتات (`.طرد البوتات`)
• `.م19` ➪ التثبيت (`.تثبيت` ، `.الغاء التثبيت`)
• `.م20` ➪ الترقية والاشراف (`.رفع مشرف`)
• `.م21` ➪ السبام والابلاغ (`.بلاغ`)
• `.م22` ➪ المحادثات الخاصة (`.كشف الخاص`)
• `.م23` ➪ الصورة الشخصية (`.صورة البروفايل`)
• `.م24` ➪ كتم المحادثات الخاصة (`.كتم خاص` ، `.فك كتم خاص`)
• `.م25` ➪ الميديا الذاتية (`.حفظ`)
• `.م26` ➪ الرتب والاصلاحات (`.رتبتي` ، `.رتبته`)
• `.م27` ➪ النظام (`.ريستارت`)
• `.م28` ➪ السرعة والاستجابة (`.بنج`)
• `.م29` ➪ إحصائيات الحساب (`.الاحصائيات`)
• `.م30` ➪ حالة الستريك (`.ستريك`)"""

# ----------------------------------------------------
# 5. أوامر المطورين
# ----------------------------------------------------

@client.on(events.NewMessage(pattern=r"^\.(اوامري|الاوامر)$"))
async def show_all_commands(event):
    if not is_sudo(event): return
    if event.out:
        await event.edit(ALL_COMMANDS_TEXT)
    else:
        await event.reply(ALL_COMMANDS_TEXT)

@client.on(events.NewMessage(pattern=r"^\.رفع مطور$"))
async def add_developer(event):
    if not event.out:  # فقط الحساب الأساسي يملك صلاحية رفع مطور جديد
        return

    if not event.is_reply:
        return await event.edit("⚠️ **يرجى الرد على رسالة الشخص أو على رسالة محولة/ممررة منه!**")

    reply = await event.get_reply_message()
    target_id = None

    if reply.forward and reply.forward.sender_id:
        target_id = reply.forward.sender_id
    elif reply.sender_id:
        target_id = reply.sender_id

    if not target_id:
        return await event.edit("❌ **تعذر التعرف على آيدي الشخص.**")

    if target_id in DEVELOPERS:
        return await event.edit("⚠️ **هذا الشخص مرفوع مطور بالفعل!**")

    DEVELOPERS.add(target_id)
    await event.edit(f"✅ **تم رفع المستخدم كمطور في السورس بنجاح!**\n🆔 الآيدي: `{target_id}`\nيمكنه الآن استخدام السورس والأوامر.")

@client.on(events.NewMessage(pattern=r"^\.تنزيل مطور$"))
async def remove_developer(event):
    if not event.out:
        return

    if not event.is_reply:
        return await event.edit("⚠️ **يرجى الرد على الشخص أو على رسالة محولة منه!**")

    reply = await event.get_reply_message()
    target_id = reply.forward.sender_id if (reply.forward and reply.forward.sender_id) else reply.sender_id

    if target_id in DEVELOPERS:
        DEVELOPERS.remove(target_id)
        await event.edit(f"✅ **تم تنزيل المستخدم من قائمة المطورين:** `{target_id}`")
    else:
        await event.edit("⚠️ **هذا الشخص ليس مطوراً بالأساس.**")

@client.on(events.NewMessage(pattern=r"^\.المطورين$"))
async def list_developers(event):
    if not is_sudo(event): return
    if not DEVELOPERS:
        msg = "ℹ️ **لا يوجد مطورين مرفوعين حالياً.**"
    else:
        devs = "\n".join([f"• `{dev_id}`" for dev_id in DEVELOPERS])
        msg = f"👑 **قائمة المطورين المرفوعين:**\n{devs}"
    
    if event.out:
        await event.edit(msg)
    else:
        await event.reply(msg)

# ----------------------------------------------------
# 6. الأوامر التنفيذية (من .م1 إلى .م30)
# ----------------------------------------------------

# --- م1 ---
@client.on(events.NewMessage(pattern=r"^\.م1$"))
async def m1(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر البحث والوسائط (`.م1`):**\n• `.صورة` [اسم البحث]\n• `.بحث` [نص البحث]\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.بحث\s+(.+)"))
async def search_cmd(event):
    if not is_sudo(event): return
    query = event.pattern_match.group(1)
    text = f"🔍 **جاري البحث عن:** `{query}`\n🔗 https://www.google.com/search?q={query.replace(' ', '+')}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.صورة\s+(.+)"))
async def search_photo(event):
    if not is_sudo(event): return
    query = event.pattern_match.group(1)
    status_msg = await event.edit(f"🔍 **جاري جلب صورة لـ:** `{query}`...") if event.out else await event.reply(f"🔍 **جاري جلب صورة لـ:** `{query}`...")
    try:
        url = "https://picsum.photos/800/600"
        await client.send_file(event.chat_id, url, caption=f"🖼 **نتائج الصور لـ:** `{query}`\n{SOURCE_TITLE}")
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit(f"❌ **حدث خطأ:** {e}")

# --- م2 ---
@client.on(events.NewMessage(pattern=r"^\.م2$"))
async def m2(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الوقت والتاريخ (`.م2`):**\n• `.الوقت`\n• `.التاريخ`\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.الوقت$"))
async def get_time(event):
    if not is_sudo(event): return
    t = datetime.datetime.now().strftime("%I:%M:%S %p")
    text = f"⏰ **الوقت الحالي:** `{t}`"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.التاريخ$"))
async def get_date(event):
    if not is_sudo(event): return
    d = datetime.datetime.now().strftime("%Y-%m-%d")
    text = f"📅 **التاريخ الحالي:** `{d}`"
    await event.edit(text) if event.out else await event.reply(text)

# --- م3 ---
@client.on(events.NewMessage(pattern=r"^\.م3$"))
async def m3(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر إدارة المجموعات (`.م3`):**\n• `.حظر` (بالرد)\n• `.فك حظر` (بالرد)\n• `.كتم` (بالرد)\n• `.فك كتم` (بالرد)\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.حظر$"))
async def ban_user(event):
    if not is_sudo(event): return
    if not event.is_reply or not event.is_group:
        msg = "⚠️ يرجى الرد على العضو داخل المجموعة."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    await client(EditBannedRequest(event.chat_id, r.sender_id, ChatBannedRights(until_date=None, view_messages=True)))
    msg = f"⛔ تم حظر المستخدم: `{r.sender_id}`"
    await event.edit(msg) if event.out else await event.reply(msg)

@client.on(events.NewMessage(pattern=r"^\.فك حظر$"))
async def unban_user(event):
    if not is_sudo(event): return
    if not event.is_reply or not event.is_group:
        msg = "⚠️ يرجى الرد على العضو داخل المجموعة."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    await client(EditBannedRequest(event.chat_id, r.sender_id, ChatBannedRights(until_date=None, view_messages=False)))
    msg = f"✅ تم فك حظر المستخدم: `{r.sender_id}`"
    await event.edit(msg) if event.out else await event.reply(msg)

@client.on(events.NewMessage(pattern=r"^\.كتم$"))
async def mute_user(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ يرجى الرد على العضو."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    MUTED_USERS.setdefault(event.chat_id, set()).add(r.sender_id)
    msg = f"🔇 تم كتم المستخدم: `{r.sender_id}`"
    await event.edit(msg) if event.out else await event.reply(msg)

@client.on(events.NewMessage(pattern=r"^\.فك كتم$"))
async def unmute_user(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ يرجى الرد على العضو."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    if event.chat_id in MUTED_USERS and r.sender_id in MUTED_USERS[event.chat_id]:
        MUTED_USERS[event.chat_id].remove(r.sender_id)
        msg = f"🔊 تم فك كتم المستخدم: `{r.sender_id}`"
    else:
        msg = "⚠️ المستخدم غير مكتوم بالأساس."
    await event.edit(msg) if event.out else await event.reply(msg)

# --- م4 ---
@client.on(events.NewMessage(pattern=r"^\.م4$"))
async def m4(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الردود التلقائية (`.م4`):**\n• `.رد` [الكلمة] = [الرد]\n• `.مسح الردود`\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.رد\s+(.+)\s+=\s+(.+)"))
async def add_reply(event):
    if not is_sudo(event): return
    w = event.pattern_match.group(1).strip()
    a = event.pattern_match.group(2).strip()
    REPLY_MAP[w] = a
    text = f"✅ تم إضافة الرد:\n`{w}` ➔ `{a}`"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.مسح الردود$"))
async def clear_replies(event):
    if not is_sudo(event): return
    REPLY_MAP.clear()
    text = "🗑️ تم مسح جميع الردود التلقائية."
    await event.edit(text) if event.out else await event.reply(text)

# --- م5 ---
@client.on(events.NewMessage(pattern=r"^\.م5$"))
async def m5(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر المسح والتنظيف (`.م5`):**\n• `.مسح` [العدد]\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

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
    text = f"📌 **أوامر لعبة الأحكام الجماعية (`.م6`):**\n• `.احكام`\n• `.لعب` (للأعضاء)\n• `.بدء`\n• `.انهاء`\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.احكام$"))
async def start_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ هذا الأمر يعمل داخل المجموعات فقط!"
        return await event.edit(msg) if event.out else await event.reply(msg)
    GAME_ACTIVE = True
    GAME_PLAYERS = []
    GAME_CHAT_ID = event.chat_id
    text = "🎲 **تم فتح باب الانضمام للعبة الأحكام!**\nأرسل `.لعب` للانضمام (الحد الأقصى 10). اكتب `.بدء` للقرعة."
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.لعب$", incoming=True))
async def join_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not GAME_ACTIVE or event.chat_id != GAME_CHAT_ID: return
    sender = await event.get_sender()
    if any(p['id'] == sender.id for p in GAME_PLAYERS): return await event.reply("⚠️ أنت منضم للعبة بالفعل!")
    if len(GAME_PLAYERS) >= 10: return await event.reply("❌ اكتمل العدد الأقصى!")
    GAME_PLAYERS.append({'id': sender.id, 'name': sender.first_name or "عضو"})
    await event.reply(f"✅ تم انضمام [{sender.first_name}](tg://user?id={sender.id}) بنجاح!")

@client.on(events.NewMessage(pattern=r"^\.بدء$"))
async def draw_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not is_sudo(event): return
    if not GAME_ACTIVE or event.chat_id != GAME_CHAT_ID:
        msg = "⚠️ اكتب `.احكام` أولاً."
        return await event.edit(msg) if event.out else await event.reply(msg)
    if len(GAME_PLAYERS) < 2:
        msg = "⚠️ يلزم عضوين على الأقل!"
        return await event.edit(msg) if event.out else await event.reply(msg)
    chosen = random.sample(GAME_PLAYERS, 2)
    text = f"👑 **الحاكم:** [{chosen[0]['name']}](tg://user?id={chosen[0]['id']})\n⚖️ **المحكوم:** [{chosen[1]['name']}](tg://user?id={chosen[1]['id']})"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.انهاء$"))
async def stop_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not is_sudo(event): return
    GAME_ACTIVE = False
    GAME_PLAYERS = []
    GAME_CHAT_ID = None
    text = "🔴 **تم إنهاء اللعبة.**"
    await event.edit(text) if event.out else await event.reply(text)

# --- م7 ---
@client.on(events.NewMessage(pattern=r"^\.م7$"))
async def m7(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر كشف الحساب والآيدي (`.م7`):**\n• `.ايدي`\n• `.فحص` (بالرد)\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.ايدي$"))
async def get_id(event):
    if not is_sudo(event): return
    if event.is_reply:
        r = await event.get_reply_message()
        text = f"🆔 **آيدي المستخدم:** `{r.sender_id}`"
    else:
        text = f"🆔 **آيديك:** `{event.sender_id}`\n💬 **آيدي الشات:** `{event.chat_id}`"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.فحص$"))
async def inspect_user(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ يرجى الرد على المستخدم."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    u = await client.get_entity(r.sender_id)
    text = f"👤 **الاسم:** {u.first_name}\n🆔 **الآيدي:** `{u.id}`\n🌐 **اليوزر:** @{u.username if u.username else 'لا يوجد'}"
    await event.edit(text) if event.out else await event.reply(text)

# --- م8 ---
@client.on(events.NewMessage(pattern=r"^\.م8$"))
async def m8(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الحظر العام (`.م8`):**\n• `.حظر عام` (بالرد)\n• `.الغاء العام` (بالرد)\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.حظر عام$"))
async def gban_user(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ يرجى الرد على الشخص."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    GBAN_SET.add(r.sender_id)
    text = f"🚫 تم حظر المستخدم عاماً: `{r.sender_id}`"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.الغاء العام$"))
async def ungban_user(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ يرجى الرد على الشخص."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    if r.sender_id in GBAN_SET:
        GBAN_SET.remove(r.sender_id)
        text = f"✅ تم إلغاء الحظر العام عن: `{r.sender_id}`"
    else:
        text = "⚠️ المستخدم غير محظور عاماً."
    await event.edit(text) if event.out else await event.reply(text)

# --- م9 ---
@client.on(events.NewMessage(pattern=r"^\.م9$"))
async def m9(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الكتم العام (`.م9`):**\n• `.كتم عام` (بالرد)\n• `.الغاء كتم عام` (بالرد)\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.كتم عام$"))
async def gmute_user(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ يرجى الرد على الشخص."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    GMUTE_SET.add(r.sender_id)
    text = f"🔇 تم كتم المستخدم عاماً: `{r.sender_id}`"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.الغاء كتم عام$"))
async def ungmute_user(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ يرجى الرد على الشخص."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    if r.sender_id in GMUTE_SET:
        GMUTE_SET.remove(r.sender_id)
        text = f"🔊 تم إلغاء الكتم العام عن: `{r.sender_id}`"
    else:
        text = "⚠️ المستخدم غير مكتوم عاماً."
    await event.edit(text) if event.out else await event.reply(text)

# --- م10 ---
@client.on(events.NewMessage(pattern=r"^\.م10$"))
async def m10(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر فحص الكروب والقنوات (`.م10`):**\n• `.الرابط` (جلب رابط المجموعة)\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.الرابط$"))
async def get_link(event):
    if not is_sudo(event): return
    try:
        link = await client(ExportChatInviteRequest(event.chat_id))
        text = f"🔗 **رابط المحادثة:** {link.link}"
    except Exception as e:
        text = f"❌ لم أستطع جلب الرابط: {e}"
    await event.edit(text) if event.out else await event.reply(text)

# --- م11 ---
@client.on(events.NewMessage(pattern=r"^\.م11$"))
async def m11(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر تغيير الاسم (`.م11`):**\n• `.اسم` [الاسم الجديد]\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.اسم\s+(.+)"))
async def update_name(event):
    if not is_sudo(event): return
    name = event.pattern_match.group(1)
    await client(functions.account.UpdateProfileRequest(first_name=name))
    text = f"✅ تم تحديث الاسم إلى: `{name}`"
    await event.edit(text) if event.out else await event.reply(text)

# --- م12 ---
@client.on(events.NewMessage(pattern=r"^\.م12$"))
async def m12(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر البايو والبروفايل (`.م12`):**\n• `.بايو` [البايو الجديد]\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.بايو\s+(.+)"))
async def update_bio(event):
    if not is_sudo(event): return
    bio = event.pattern_match.group(1)
    await client(functions.account.UpdateProfileRequest(about=bio))
    text = f"✅ تم تحديث البايو إلى:\n`{bio}`"
    await event.edit(text) if event.out else await event.reply(text)

# --- م13 ---
@client.on(events.NewMessage(pattern=r"^\.م13$"))
async def m13(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر حظر الكلمات (`.م13`):**\n• `.منع` [الكلمة]\n• `.قائمة المنع`\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.منع\s+(.+)"))
async def block_word(event):
    if not is_sudo(event): return
    word = event.pattern_match.group(1).strip()
    BLOCKED_WORDS.add(word)
    text = f"🚫 تم إضافة الكلمة لمصفوفة المنع: `{word}`"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.قائمة المنع$"))
async def list_blocked(event):
    if not is_sudo(event): return
    if not BLOCKED_WORDS:
        msg = "⚠️ لا توجد كلمات ممنوعة."
    else:
        words = "\n".join([f"• `{w}`" for w in BLOCKED_WORDS])
        msg = f"📜 **الكلمات الممنوعة:**\n{words}"
    await event.edit(msg) if event.out else await event.reply(msg)

# --- م14 ---
@client.on(events.NewMessage(pattern=r"^\.م14$"))
async def m14(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر المغادرة والانضمام (`.م14`):**\n• `.مغادرة`\n• `.انضمام` [رابط أو يوزر المحادثة]\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.مغادرة$"))
async def leave_chat(event):
    if not is_sudo(event): return
    msg = await event.edit("👋 جاري المغادرة...") if event.out else await event.reply("👋 جاري المغادرة...")
    await client(LeaveChannelRequest(event.chat_id))

@client.on(events.NewMessage(pattern=r"^\.انضمام\s+(.+)"))
async def join_chat(event):
    if not is_sudo(event): return
    link = event.pattern_match.group(1).strip()
    status_msg = await event.edit("⏳ **جاري الانضمام للمحادثة...**") if event.out else await event.reply("⏳ **جاري الانضمام للمحادثة...**")
    try:
        if "joinchat/" in link or "+" in link:
            hash_val = link.split("+")[-1].split("joinchat/")[-1]
            await client(ImportChatInviteRequest(hash_val))
        else:
            username = link.split("/")[-1].replace("@", "")
            await client(JoinChannelRequest(username))
        await status_msg.edit("✅ **تم الانضمام بنجاح!**")
    except Exception as e:
        await status_msg.edit(f"❌ **فشل الانضمام:** {e}")

# --- م15 ---
@client.on(events.NewMessage(pattern=r"^\.م15$"))
async def m15(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر إنشاء الكروبات والقنوات (`.م15`):**\n• `.انشاء كروب` [الاسم]\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.انشاء كروب\s+(.+)"))
async def create_group(event):
    if not is_sudo(event): return
    title = event.pattern_match.group(1)
    await client(CreateChannelRequest(title=title, about="تم إنشاؤه عبر السورس", megagroup=True))
    text = f"✅ تم إنشاء المجموعة بنجاح: `{title}`"
    await event.edit(text) if event.out else await event.reply(text)

# --- م16 (إضافة الأعضاء + حذف الجهات) ---
@client.on(events.NewMessage(pattern=r"^\.م16$"))
async def m16(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الإضافة والحذف للجهات (`.م16`):**\n• `.ضيف` [رابط الكروب المراد السحب منه]\n• `.حذف الجهات` [رابط الكروب لحذفهم من جهات الاتصال]\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.ضيف\s+(.+)"))
async def add_contacts_then_group(event):
    if not is_sudo(event): return
    target = event.pattern_match.group(1).strip()
    if not event.is_group:
        msg = "⚠️ يرجى استخدام هذا الأمر داخل المجموعة التي تريد إضافة الأعضاء إليها!"
        return await event.edit(msg) if event.out else await event.reply(msg)

    status_msg = await event.edit("⏳ **جاري سحب الأعضاء وبدء الإضافة...**") if event.out else await event.reply("⏳ **جاري سحب الأعضاء وبدء الإضافة...**")

    try:
        if "joinchat/" in target or "+" in target:
            hash_val = target.split("+")[-1].split("joinchat/")[-1]
            updates = await client(ImportChatInviteRequest(hash_val))
            entity = updates.chats[0]
        else:
            username = target.split("/")[-1].replace("@", "")
            entity = await client.get_entity(username)

        users = await client.get_participants(entity)
        if not users:
            return await status_msg.edit("❌ **لم يتم العثور على أعضاء أو أن الأعضاء مخفيين.**")

        added_to_group = 0
        failed = 0

        for u in users:
            if u.bot or u.deleted or u.is_self:
                continue
            try:
                await client(InviteToChannelRequest(event.chat_id, [u]))
                added_to_group += 1
                
                if added_to_group % 2 == 0:
                    await status_msg.edit(f"⏳ **جاري الإضافة...**\n👥 تم إضافة: `{added_to_group}` عضواً")
                
                await asyncio.sleep(4)
                
            except Exception as e:
                failed += 1
                err_str = str(e)
                if "PEER_FLOOD" in err_str or "USER_RESTRICTED" in err_str:
                    return await status_msg.edit("❌ **توقف السكربت! الحساب الأساسي محظور حالياً من إضافة الأعضاء (PeerFlood).**")
                elif "CHAT_ADMIN_REQUIRED" in err_str:
                    return await status_msg.edit("❌ **توقف السكربت! الحساب يحتاج صلاحيات أدمن لإضافة أعضاء.**")
            
            if added_to_group >= 30:
                break

        await status_msg.edit(f"✅ **اكتملت العملية!**\n👥 تم إضافة: `{added_to_group}`\n❌ أخطاء/تجاهل: `{failed}`")

    except Exception as err:
        await status_msg.edit(f"❌ **حدث خطأ في الجلب:**\n`{err}`")

@client.on(events.NewMessage(pattern=r"^\.حذف الجهات\s+(.+)"))
async def delete_added_contacts(event):
    if not is_sudo(event): return
    target = event.pattern_match.group(1).strip()
    status_msg = await event.edit("⏳ **جاري جلب الأعضاء وحذفهم من جهات الاتصال...**") if event.out else await event.reply("⏳ **جاري جلب الأعضاء وحذفهم من جهات الاتصال...**")
    try:
        if "joinchat/" in target or "+" in target:
            hash_val = target.split("+")[-1].split("joinchat/")[-1]
            updates = await client(ImportChatInviteRequest(hash_val))
            entity = updates.chats[0]
        else:
            username = target.split("/")[-1].replace("@", "")
            entity = await client.get_entity(username)

        users = await client.get_participants(entity)
        if not users:
            return await status_msg.edit("❌ **لم يتم العثور على أعضاء.**")

        deleted_count = 0
        failed = 0

        for u in users:
            if u.bot or u.deleted or u.is_self:
                continue
            try:
                await client(functions.contacts.DeleteContactsRequest(id=[u]))
                deleted_count += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                failed += 1

        await status_msg.edit(f"✅ **تم الانتهاء من حذف الجهات بنجاح!**\n🗑️ تم حذفهم من جهات الاتصال: `{deleted_count}`\n❌ فشل/غير موجودين: `{failed}`")

    except Exception as err:
        await status_msg.edit(f"❌ **حدث خطأ:**\n`{err}`")

# --- م17 ---
@client.on(events.NewMessage(pattern=r"^\.م17$"))
async def m17(event):
    if not is_sudo(event): return
    text = f"📌 **تنظيف الحسابات المغلقة (`.م17`):**\n• `.تنظيف المغلقة`\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.تنظيف المغلقة$"))
async def clean_deleted(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ للمجموعات فقط."
        return await event.edit(msg) if event.out else await event.reply(msg)
    status_msg = await event.edit("🔍 جاري فحص الحسابات المحذوفة...") if event.out else await event.reply("🔍 جاري فحص الحسابات المحذوفة...")
    users = await client.get_participants(event.chat_id)
    c = 0
    for u in users:
        if u.deleted:
            try:
                await client(EditBannedRequest(event.chat_id, u.id, ChatBannedRights(until_date=None, view_messages=True)))
                c += 1
            except: pass
    await status_msg.edit(f"🧹 تم طرد `{c}` حساب محذوف.")

# --- م18 ---
@client.on(events.NewMessage(pattern=r"^\.م18$"))
async def m18(event):
    if not is_sudo(event): return
    text = f"📌 **طرد البوتات (`.م18`):**\n• `.طرد البوتات`\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.طرد البوتات$"))
async def purge_bots(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ للمجموعات فقط."
        return await event.edit(msg) if event.out else await event.reply(msg)
    status_msg = await event.edit("🔍 جاري طرد البوتات...") if event.out else await event.reply("🔍 جاري طرد البوتات...")
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
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.تثبيت$"))
async def pin_msg(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ بالرد على الرسالة."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    await client.pin_message(event.chat_id, r.id)
    msg = "📌 تم تثبيت الرسالة بنجاح."
    await event.edit(msg) if event.out else await event.reply(msg)

@client.on(events.NewMessage(pattern=r"^\.الغاء التثبيت$"))
async def unpin_msg(event):
    if not is_sudo(event): return
    await client.unpin_message(event.chat_id)
    msg = "📌 تم إلغاء تثبيت الرسالة الأخيرة."
    await event.edit(msg) if event.out else await event.reply(msg)

# --- م20 ---
@client.on(events.NewMessage(pattern=r"^\.م20$"))
async def m20(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الإشراف والترقية (`.م20`):**\n• `.رفع مشرف` (بالرد)\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.رفع مشرف$"))
async def promote_user(event):
    if not is_sudo(event): return
    if not event.is_reply or not event.is_group:
        msg = "⚠️ بالرد على الرسالة في مجموعة."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    rights = ChatAdminRights(
        post_messages=True, edit_messages=True, delete_messages=True,
        ban_users=True, invite_users=True, pin_messages=True, add_admins=False
    )
    await client(EditAdminRequest(event.chat_id, r.sender_id, rights, custom_title="مشرف"))
    text = f"👑 تم ترقية المستخدم: `{r.sender_id}` مشرفاً."
    await event.edit(text) if event.out else await event.reply(text)

# --- م21 ---
@client.on(events.NewMessage(pattern=r"^\.م21$"))
async def m21(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر الإبلاغ والسبام (`.م21`):**\n• `.بلاغ` (بالرد)\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.بلاغ$"))
async def report_spam(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ بالرد على الرسالة المخالفة."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    await client(ReportSpamRequest(peer=r.sender_id))
    text = "🚨 تم رفع بلاغ سبام للتليجرام عن هذا المستخدم."
    await event.edit(text) if event.out else await event.reply(text)

# --- م22 ---
@client.on(events.NewMessage(pattern=r"^\.م22$"))
async def m22(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر المحادثات الخاصة (`.م22`):**\n• `.كشف الخاص`\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.كشف الخاص$"))
async def inspect_pms(event):
    if not is_sudo(event): return
    status_msg = await event.edit("🔍 جاري جلب قائمة أحدث المحادثات الخاصة...") if event.out else await event.reply("🔍 جاري جلب قائمة أحدث المحادثات الخاصة...")
    dialogs = await client.get_dialogs(limit=20)
    text = "💬 **أحدث المحادثات الخاصة:**\n"
    count = 0
    for d in dialogs:
        if d.is_user and not d.entity.bot:
            count += 1
            text += f"{count}. {d.name} ➔ (`{d.id}`)\n"
            if count >= 10: break
    await status_msg.edit(text)

# --- م23 ---
@client.on(events.NewMessage(pattern=r"^\.م23$"))
async def m23(event):
    if not is_sudo(event): return
    text = f"📌 **صورة البروفايل (`.م23`):**\n• `.صورة البروفايل` (بالرد على صورة)\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.صورة البروفايل$"))
async def set_profile_photo(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ يرجى الرد على الصورة."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    if not r.photo:
        msg = "⚠️ الرسالة المردود عليها ليست صورة!"
        return await event.edit(msg) if event.out else await event.reply(msg)
    status_msg = await event.edit("⏳ جاري تعيين صورة البروفايل...") if event.out else await event.reply("⏳ جاري تعيين صورة البروفايل...")
    photo = await r.download_media()
    file = await client.upload_file(photo)
    await client(functions.photos.UploadProfilePhotoRequest(file=file))
    if os.path.exists(photo): os.remove(photo)
    await status_msg.edit("🖼 تم تغيير صورة بروفايلك بنجاح!")

# --- م24 ---
@client.on(events.NewMessage(pattern=r"^\.م24$"))
async def m24(event):
    if not is_sudo(event): return
    text = f"📌 **كتم المحادثات الخاصة (`.م24`):**\n• `.كتم خاص` (في الخاص أو بالرد)\n• `.فك كتم خاص`\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.كتم خاص$"))
async def mute_pm(event):
    if not is_sudo(event): return
    target_id = None
    if event.is_private:
        target_id = event.chat_id
    elif event.is_reply:
        r = await event.get_reply_message()
        target_id = r.sender_id
    if not target_id:
        msg = "⚠️ هذا الأمر في الخاص أو بالرد على شخص."
        return await event.edit(msg) if event.out else await event.reply(msg)
    MUTED_PMS.add(target_id)
    text = f"🔇 تم كتم الشخص في الخاص: `{target_id}`"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.فك كتم خاص$"))
async def unmute_pm(event):
    if not is_sudo(event): return
    target_id = None
    if event.is_private:
        target_id = event.chat_id
    elif event.is_reply:
        r = await event.get_reply_message()
        target_id = r.sender_id
    if target_id in MUTED_PMS:
        MUTED_PMS.remove(target_id)
        text = f"🔊 تم فك كتم الخاص عن: `{target_id}`"
    else:
        text = "⚠️ الشخص ليس مكتوماً في الخاص."
    await event.edit(text) if event.out else await event.reply(text)

# --- م25 ---
@client.on(events.NewMessage(pattern=r"^\.م25$"))
async def m25(event):
    if not is_sudo(event): return
    text = f"📌 **حفظ الميديا الذاتية (`.م25`):**\n• `.حفظ` (بالرد على الصورة/الفيديو المؤقت)\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.حفظ$"))
async def save_self_destruct(event):
    if not is_sudo(event): return
    if not event.is_reply:
        msg = "⚠️ بالرد على الميديا المؤقتة."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    if not (r.photo or r.video or r.media):
        msg = "⚠️ الرسالة لا تحتوي وسائط!"
        return await event.edit(msg) if event.out else await event.reply(msg)
    status_msg = await event.edit("⏳ جاري تحميل الميديا وحفظها...") if event.out else await event.reply("⏳ جاري تحميل الميديا وحفظها...")
    file_path = await r.download_media()
    await client.send_file("me", file_path, caption=f"📥 **تم حفظ الوسائط بنجاح.**\n{SOURCE_TITLE}")
    if os.path.exists(file_path): os.remove(file_path)
    await status_msg.edit("✅ **تم تحميل الميديا وإرسالها لـ الرسائل المحفوظة (Saved Messages)!**")

# --- م26 ---
@client.on(events.NewMessage(pattern=r"^\.م26$"))
async def m26(event):
    if not is_sudo(event): return
    text = f"📌 **معرفة رتب الأعضاء (`.م26`):**\n• `.رتبتي`\n• `.رتبته` (بالرد)\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.رتبتي$"))
async def my_rank(event):
    if not is_sudo(event): return
    if not event.is_group:
        msg = "⚠️ داخل المجموعات فقط."
        return await event.edit(msg) if event.out else await event.reply(msg)
    perms = await client.get_permissions(event.chat_id, event.sender_id)
    if perms.is_creator: rank = "👑 المالك الأساسي"
    elif perms.is_admin: rank = "🛡 مشرف في المجموعة"
    else: rank = "👤 عضو عادي"
    text = f"📊 **رتبتك في الكروب:** {rank}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.رتبته$"))
async def user_rank(event):
    if not is_sudo(event): return
    if not event.is_reply or not event.is_group:
        msg = "⚠️ بالرد داخل مجموعة."
        return await event.edit(msg) if event.out else await event.reply(msg)
    r = await event.get_reply_message()
    perms = await client.get_permissions(event.chat_id, r.sender_id)
    if perms.is_creator: rank = "👑 المالك الأساسي"
    elif perms.is_admin: rank = "🛡 مشرف في المجموعة"
    else: rank = "👤 عضو عادي"
    text = f"📊 **رتبة المستخدم:** {rank}"
    await event.edit(text) if event.out else await event.reply(text)

# --- م27 ---
@client.on(events.NewMessage(pattern=r"^\.م27$"))
async def m27(event):
    if not is_sudo(event): return
    text = f"📌 **أوامر السورس والنظام (`.م27`):**\n• `.ريستارت` (إعادة تشغيل البوت)\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.ريستارت$"))
async def restart_bot(event):
    if not is_sudo(event): return
    msg = await event.edit("🔄 **جاري إعادة تشغيل السورس...**") if event.out else await event.reply("🔄 **جاري إعادة تشغيل السورس...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

# --- م28 ---
@client.on(events.NewMessage(pattern=r"^\.م28$"))
async def m28(event):
    if not is_sudo(event): return
    text = f"📌 **قياس سرعة السيرفر (`.م28`):**\n• `.بنج`\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.بنج$"))
async def ping_cmd(event):
    if not is_sudo(event): return
    start = datetime.datetime.now()
    status_msg = await event.edit("🚀 **PONG!**") if event.out else await event.reply("🚀 **PONG!**")
    end = datetime.datetime.now()
    ms = (end - start).microseconds / 1000
    await status_msg.edit(f"⚡ **استجابة السورس:** `{ms:.2f}ms`\n{SOURCE_TITLE}")

# --- م29 ---
@client.on(events.NewMessage(pattern=r"^\.م29$"))
async def m29(event):
    if not is_sudo(event): return
    text = f"📌 **إحصائيات الحساب (`.م29`):**\n• `.الاحصائيات`\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.الاحصائيات$"))
async def user_stats(event):
    if not is_sudo(event): return
    status_msg = await event.edit("⏳ جاري تحليل وتجميع الإحصائيات...") if event.out else await event.reply("⏳ جاري تحليل وتجميع الإحصائيات...")
    dialogs = await client.get_dialogs()
    pms, groups, channels = 0, 0, 0
    for d in dialogs:
        if d.is_user: pms += 1
        elif d.is_group: groups += 1
        elif d.is_channel: channels += 1
    await status_msg.edit(f"📊 **إحصائيات حسابك الشاملة:**\n💬 **المحادثات الخاصة:** `{pms}`\n👥 **المجموعات:** `{groups}`\n📢 **القنوات:** `{channels}`")

# --- م30 ---
@client.on(events.NewMessage(pattern=r"^\.م30$"))
async def m30(event):
    if not is_sudo(event): return
    text = f"📌 **الستريك وحالة السورس (`.م30`):**\n• `.ستريك`\n\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

@client.on(events.NewMessage(pattern=r"^\.ستريك$"))
async def streak_status(event):
    if not is_sudo(event): return
    text = f"🔥 **وضع الستريك:** شغال بدون انقطاع ✅\n{SOURCE_TITLE}"
    await event.edit(text) if event.out else await event.reply(text)

# ----------------------------------------------------
# 7. الحارس التلقائي (المراقبة والمعالجة الشاملة)
# ----------------------------------------------------
@client.on(events.NewMessage(incoming=True))
async def global_watcher(event):
    sender_id = event.sender_id
    if not sender_id: return

    # عدم تطبيق المراقبة على صاحب الحساب أو المطورين
    if is_sudo(event):
        return

    # 1. الحظر العام (حذف وطرد)
    if sender_id in GBAN_SET:
        try:
            await event.delete()
            if event.is_group:
                await client(EditBannedRequest(event.chat_id, sender_id, ChatBannedRights(until_date=None, view_messages=True)))
        except: pass
        return

    # 2. الكتم العام والكتم المحلي
    if sender_id in GMUTE_SET or (event.chat_id in MUTED_USERS and sender_id in MUTED_USERS[event.chat_id]):
        try: await event.delete()
        except: pass
        return

    # 3. كتم الخاص
    if event.is_private and sender_id in MUTED_PMS:
        try: await event.delete()
        except: pass
        return

    # 4. منع الكلمات
    if event.raw_text:
        for w in BLOCKED_WORDS:
            if w in event.raw_text:
                try: await event.delete()
                except: pass
                return

    # 5. الردود التلقائية
    if event.raw_text in REPLY_MAP:
        await event.reply(REPLY_MAP[event.raw_text])

# ----------------------------------------------------
# 8. تشغيل الحساب
# ----------------------------------------------------
print(f"⚡ {SOURCE_TITLE} يعمل بنجاح! ⚡")
client.start()
client.run_until_disconnected()

