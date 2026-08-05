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

GAME_ACTIVE = False
GAME_PLAYERS = []
GAME_CHAT_ID = None

# ----------------------------------------------------
# 3. قائمة الأوامر الكاملة
# ----------------------------------------------------
ALL_COMMANDS_TEXT = f"""✦─────『 {SOURCE_TITLE} 』─────✦

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
• `.م16` ➪ نقل ونقل الاعضاء (`.ضيف [رابط كروب]`)
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
# 4. الأوامر من .م1 إلى .م30 تنفيذاً وكوداً
# ----------------------------------------------------

@client.on(events.NewMessage(pattern=r"^\.(اوامري|الاوامر)$", outgoing=True))
async def show_all_commands(event):
    await event.edit(ALL_COMMANDS_TEXT)

# --- م1 ---
@client.on(events.NewMessage(pattern=r"^\.م1$", outgoing=True))
async def m1(event):
    await event.edit(f"📌 **أوامر البحث والوسائط (`.م1`):**\n• `.صورة` [اسم البحث]\n• `.بحث` [نص البحث]\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.بحث\s+(.+)", outgoing=True))
async def search_cmd(event):
    query = event.pattern_match.group(1)
    await event.edit(f"🔍 **جاري البحث عن:** `{query}`\n🔗 https://www.google.com/search?q={query.replace(' ', '+')}")

@client.on(events.NewMessage(pattern=r"^\.صورة\s+(.+)", outgoing=True))
async def search_photo(event):
    query = event.pattern_match.group(1)
    await event.edit(f"🔍 **جاري جلب صورة لـ:** `{query}`...")
    try:
        url = f"https://picsum.photos/800/600"
        await client.send_file(event.chat_id, url, caption=f"🖼 **نتائج الصور لـ:** `{query}`\n{SOURCE_TITLE}")
        await event.delete()
    except Exception as e:
        await event.edit(f"❌ **حدث خطأ:** {e}")

# --- م2 ---
@client.on(events.NewMessage(pattern=r"^\.م2$", outgoing=True))
async def m2(event):
    await event.edit(f"📌 **أوامر الوقت والتاريخ (`.م2`):**\n• `.الوقت`\n• `.التاريخ`\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.الوقت$", outgoing=True))
async def get_time(event):
    t = datetime.datetime.now().strftime("%I:%M:%S %p")
    await event.edit(f"⏰ **الوقت الحالي:** `{t}`")

@client.on(events.NewMessage(pattern=r"^\.التاريخ$", outgoing=True))
async def get_date(event):
    d = datetime.datetime.now().strftime("%Y-%m-%d")
    await event.edit(f"📅 **التاريخ الحالي:** `{d}`")

# --- م3 ---
@client.on(events.NewMessage(pattern=r"^\.م3$", outgoing=True))
async def m3(event):
    await event.edit(f"📌 **أوامر إدارة المجموعات (`.م3`):**\n• `.حظر` (بالرد)\n• `.فك حظر` (بالرد)\n• `.كتم` (بالرد)\n• `.فك كتم` (بالرد)\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.حظر$", outgoing=True))
async def ban_user(event):
    if not event.is_reply or not event.is_group:
        return await event.edit("⚠️ يرجى الرد على العضو داخل المجموعة.")
    r = await event.get_reply_message()
    await client(EditBannedRequest(event.chat_id, r.sender_id, ChatBannedRights(until_date=None, view_messages=True)))
    await event.edit(f"⛔ تم حظر المستخدم: `{r.sender_id}`")

@client.on(events.NewMessage(pattern=r"^\.فك حظر$", outgoing=True))
async def unban_user(event):
    if not event.is_reply or not event.is_group:
        return await event.edit("⚠️ يرجى الرد على العضو داخل المجموعة.")
    r = await event.get_reply_message()
    await client(EditBannedRequest(event.chat_id, r.sender_id, ChatBannedRights(until_date=None, view_messages=False)))
    await event.edit(f"✅ تم فك حظر المستخدم: `{r.sender_id}`")

@client.on(events.NewMessage(pattern=r"^\.كتم$", outgoing=True))
async def mute_user(event):
    if not event.is_reply:
        return await event.edit("⚠️ يرجى الرد على العضو.")
    r = await event.get_reply_message()
    MUTED_USERS.setdefault(event.chat_id, set()).add(r.sender_id)
    await event.edit(f"🔇 تم كتم المستخدم: `{r.sender_id}`")

@client.on(events.NewMessage(pattern=r"^\.فك كتم$", outgoing=True))
async def unmute_user(event):
    if not event.is_reply:
        return await event.edit("⚠️ يرجى الرد على العضو.")
    r = await event.get_reply_message()
    if event.chat_id in MUTED_USERS and r.sender_id in MUTED_USERS[event.chat_id]:
        MUTED_USERS[event.chat_id].remove(r.sender_id)
        await event.edit(f"🔊 تم فك كتم المستخدم: `{r.sender_id}`")
    else:
        await event.edit("⚠️ المستخدم غير مكتوم بالأساس.")

# --- م4 ---
@client.on(events.NewMessage(pattern=r"^\.م4$", outgoing=True))
async def m4(event):
    await event.edit(f"📌 **أوامر الردود التلقائية (`.م4`):**\n• `.رد` [الكلمة] = [الرد]\n• `.مسح الردود`\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.رد\s+(.+)\s+=\s+(.+)", outgoing=True))
async def add_reply(event):
    w = event.pattern_match.group(1).strip()
    a = event.pattern_match.group(2).strip()
    REPLY_MAP[w] = a
    await event.edit(f"✅ تم إضافة الرد:\n`{w}` ➔ `{a}`")

@client.on(events.NewMessage(pattern=r"^\.مسح الردود$", outgoing=True))
async def clear_replies(event):
    REPLY_MAP.clear()
    await event.edit("🗑️ تم مسح جميع الردود التلقائية.")

# --- م5 ---
@client.on(events.NewMessage(pattern=r"^\.م5$", outgoing=True))
async def m5(event):
    await event.edit(f"📌 **أوامر المسح والتنظيف (`.م5`):**\n• `.مسح` [العدد]\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.مسح\s+(\d+)$", outgoing=True))
async def purge_messages(event):
    num = int(event.pattern_match.group(1))
    await event.delete()
    msgs = await client.get_messages(event.chat_id, limit=num)
    await client.delete_messages(event.chat_id, msgs)

# --- م6 ---
@client.on(events.NewMessage(pattern=r"^\.م6$", outgoing=True))
async def m6(event):
    await event.edit(f"📌 **أوامر لعبة الأحكام الجماعية (`.م6`):**\n• `.احكام`\n• `.لعب` (للأعضاء)\n• `.بدء`\n• `.انهاء`\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.احكام$", outgoing=True))
async def start_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not event.is_group:
        return await event.edit("⚠️ هذا الأمر يعمل داخل المجموعات فقط!")
    GAME_ACTIVE = True
    GAME_PLAYERS = []
    GAME_CHAT_ID = event.chat_id
    await event.edit("🎲 **تم فتح باب الانضمام للعبة الأحكام!**\nأرسل `.لعب` للانضمام (الحد الأقصى 10). اكتب `.بدء` للقرعة.")

@client.on(events.NewMessage(pattern=r"^\.لعب$", incoming=True))
async def join_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not GAME_ACTIVE or event.chat_id != GAME_CHAT_ID: return
    sender = await event.get_sender()
    if any(p['id'] == sender.id for p in GAME_PLAYERS): return await event.reply("⚠️ أنت منضم للعبة بالفعل!")
    if len(GAME_PLAYERS) >= 10: return await event.reply("❌ اكتمل العدد الأقصى!")
    GAME_PLAYERS.append({'id': sender.id, 'name': sender.first_name or "عضو"})
    await event.reply(f"✅ تم انضمام [{sender.first_name}](tg://user?id={sender.id}) بنجاح!")

@client.on(events.NewMessage(pattern=r"^\.بدء$", outgoing=True))
async def draw_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not GAME_ACTIVE or event.chat_id != GAME_CHAT_ID: return await event.edit("⚠️ اكتب `.احكام` أولاً.")
    if len(GAME_PLAYERS) < 2: return await event.edit("⚠️ يلزم عضوين على الأقل!")
    chosen = random.sample(GAME_PLAYERS, 2)
    await event.edit(f"👑 **الحاكم:** [{chosen[0]['name']}](tg://user?id={chosen[0]['id']})\n⚖️ **المحكوم:** [{chosen[1]['name']}](tg://user?id={chosen[1]['id']})")

@client.on(events.NewMessage(pattern=r"^\.انهاء$", outgoing=True))
async def stop_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    GAME_ACTIVE = False
    GAME_PLAYERS = []
    GAME_CHAT_ID = None
    await event.edit("🔴 **تم إنهاء اللعبة.**")

# --- م7 ---
@client.on(events.NewMessage(pattern=r"^\.م7$", outgoing=True))
async def m7(event):
    await event.edit(f"📌 **أوامر كشف الحساب والآيدي (`.م7`):**\n• `.ايدي`\n• `.فحص` (بالرد)\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.ايدي$", outgoing=True))
async def get_id(event):
    if event.is_reply:
        r = await event.get_reply_message()
        await event.edit(f"🆔 **آيدي المستخدم:** `{r.sender_id}`")
    else:
        await event.edit(f"🆔 **آيديك:** `{event.sender_id}`\n💬 **آيدي الشات:** `{event.chat_id}`")

@client.on(events.NewMessage(pattern=r"^\.فحص$", outgoing=True))
async def inspect_user(event):
    if not event.is_reply: return await event.edit("⚠️ يرجى الرد على المستخدم.")
    r = await event.get_reply_message()
    u = await client.get_entity(r.sender_id)
    await event.edit(f"👤 **الاسم:** {u.first_name}\n🆔 **الآيدي:** `{u.id}`\n🌐 **اليوزر:** @{u.username if u.username else 'لا يوجد'}")

# --- م8 ---
@client.on(events.NewMessage(pattern=r"^\.م8$", outgoing=True))
async def m8(event):
    await event.edit(f"📌 **أوامر الحظر العام (`.م8`):**\n• `.حظر عام` (بالرد)\n• `.الغاء العام` (بالرد)\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.حظر عام$", outgoing=True))
async def gban_user(event):
    if not event.is_reply: return await event.edit("⚠️ يرجى الرد على الشخص.")
    r = await event.get_reply_message()
    GBAN_SET.add(r.sender_id)
    await event.edit(f"🚫 تم حظر المستخدم عاماً: `{r.sender_id}`")

@client.on(events.NewMessage(pattern=r"^\.الغاء العام$", outgoing=True))
async def ungban_user(event):
    if not event.is_reply: return await event.edit("⚠️ يرجى الرد على الشخص.")
    r = await event.get_reply_message()
    if r.sender_id in GBAN_SET:
        GBAN_SET.remove(r.sender_id)
        await event.edit(f"✅ تم إلغاء الحظر العام عن: `{r.sender_id}`")

# --- م9 ---
@client.on(events.NewMessage(pattern=r"^\.م9$", outgoing=True))
async def m9(event):
    await event.edit(f"📌 **أوامر الكتم العام (`.م9`):**\n• `.كتم عام` (بالرد)\n• `.الغاء كتم عام` (بالرد)\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.كتم عام$", outgoing=True))
async def gmute_user(event):
    if not event.is_reply: return await event.edit("⚠️ يرجى الرد على الشخص.")
    r = await event.get_reply_message()
    GMUTE_SET.add(r.sender_id)
    await event.edit(f"🔇 تم كتم المستخدم عاماً: `{r.sender_id}`")

@client.on(events.NewMessage(pattern=r"^\.الغاء كتم عام$", outgoing=True))
async def ungmute_user(event):
    if not event.is_reply: return await event.edit("⚠️ يرجى الرد على الشخص.")
    r = await event.get_reply_message()
    if r.sender_id in GMUTE_SET:
        GMUTE_SET.remove(r.sender_id)
        await event.edit(f"🔊 تم إلغاء الكتم العام عن: `{r.sender_id}`")

# --- م10 ---
@client.on(events.NewMessage(pattern=r"^\.م10$", outgoing=True))
async def m10(event):
    await event.edit(f"📌 **أوامر فحص الكروب والقنوات (`.م10`):**\n• `.الرابط` (جلب رابط المجموعة)\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.الرابط$", outgoing=True))
async def get_link(event):
    try:
        link = await client(ExportChatInviteRequest(event.chat_id))
        await event.edit(f"🔗 **رابط المحادثة:** {link.link}")
    except Exception as e:
        await event.edit(f"❌ لم أستطع جلب الرابط: {e}")

# --- م11 ---
@client.on(events.NewMessage(pattern=r"^\.م11$", outgoing=True))
async def m11(event):
    await event.edit(f"📌 **أوامر تغيير الاسم (`.م11`):**\n• `.اسم` [الاسم الجديد]\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.اسم\s+(.+)", outgoing=True))
async def update_name(event):
    name = event.pattern_match.group(1)
    await client(functions.account.UpdateProfileRequest(first_name=name))
    await event.edit(f"✅ تم تحديث الاسم إلى: `{name}`")

# --- م12 ---
@client.on(events.NewMessage(pattern=r"^\.م12$", outgoing=True))
async def m12(event):
    await event.edit(f"📌 **أوامر البايو والبروفايل (`.م12`):**\n• `.بايو` [البايو الجديد]\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.بايو\s+(.+)", outgoing=True))
async def update_bio(event):
    bio = event.pattern_match.group(1)
    await client(functions.account.UpdateProfileRequest(about=bio))
    await event.edit(f"✅ تم تحديث البايو إلى:\n`{bio}`")

# --- م13 ---
@client.on(events.NewMessage(pattern=r"^\.م13$", outgoing=True))
async def m13(event):
    await event.edit(f"📌 **أوامر حظر الكلمات (`.م13`):**\n• `.منع` [الكلمة]\n• `.قائمة المنع`\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.منع\s+(.+)", outgoing=True))
async def block_word(event):
    word = event.pattern_match.group(1).strip()
    BLOCKED_WORDS.add(word)
    await event.edit(f"🚫 تم إضافة الكلمة لمصفوفة المنع: `{word}`")

@client.on(events.NewMessage(pattern=r"^\.قائمة المنع$", outgoing=True))
async def list_blocked(event):
    if not BLOCKED_WORDS: return await event.edit("⚠️ لا توجد كلمات ممنوعة.")
    words = "\n".join([f"• `{w}`" for w in BLOCKED_WORDS])
    await event.edit(f"📜 **الكلمات الممنوعة:**\n{words}")

# --- م14 ---
@client.on(events.NewMessage(pattern=r"^\.م14$", outgoing=True))
async def m14(event):
    await event.edit(f"📌 **أوامر المغادرة والانضمام (`.م14`):**\n• `.مغادرة`\n• `.انضمام` [رابط أو يوزر المحادثة]\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.مغادرة$", outgoing=True))
async def leave_chat(event):
    await event.edit("👋 جاري المغادرة...")
    await client(LeaveChannelRequest(event.chat_id))

@client.on(events.NewMessage(pattern=r"^\.انضمام\s+(.+)", outgoing=True))
async def join_chat(event):
    link = event.pattern_match.group(1).strip()
    await event.edit("⏳ **جاري الانضمام للمحادثة...**")
    try:
        if "joinchat/" in link or "+" in link:
            hash_val = link.split("+")[-1].split("joinchat/")[-1]
            await client(ImportChatInviteRequest(hash_val))
        else:
            username = link.split("/")[-1].replace("@", "")
            await client(JoinChannelRequest(username))
        await event.edit("✅ **تم الانضمام بنجاح!**")
    except Exception as e:
        await event.edit(f"❌ **فشل الانضمام:** {e}")

# --- م15 ---
@client.on(events.NewMessage(pattern=r"^\.م15$", outgoing=True))
async def m15(event):
    await event.edit(f"📌 **أوامر إنشاء الكروبات والقنوات (`.م15`):**\n• `.انشاء كروب` [الاسم]\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.انشاء كروب\s+(.+)", outgoing=True))
async def create_group(event):
    title = event.pattern_match.group(1)
    await client(CreateChannelRequest(title=title, about="تم إنشاؤه عبر السورس", megagroup=True))
    await event.edit(f"✅ تم إنشاء المجموعة بنجاح: `{title}`")

# --- م16 ---
@client.on(events.NewMessage(pattern=r"^\.م16$", outgoing=True))
async def m16(event):
    await event.edit(f"📌 **أوامر إضافة الأعضاء (`.م16`):**\n• `.ضيف` [رابط الكروب]\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.ضيف\s+(.+)", outgoing=True))
async def add_members(event):
    target = event.pattern_match.group(1).strip()
    if event.is_private:
        return await event.edit("⚠️ **هذا الأمر يعمل داخل المجموعات فقط.**")
    
    await event.edit("⏳ **جاري جلب الأعضاء وبدء السحب (كعضو عادي)...**")
    
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
            return await event.edit("❌ **لم يتم العثور على أعضاء أو الأعضاء مخفيين في هذا الكروب.**")

        added = 0
        failed = 0
        restricted = 0

        for u in users:
            if u.bot or u.deleted or u.is_self:
                continue
            try:
                # محاولة الإضافة (بدون اشتراط كون الحساب مشرفاً)
                result = await client(InviteToChannelRequest(channel=event.chat_id, users=[u]))
                
                if result and getattr(result, 'users', None):
                    added += 1
                else:
                    restricted += 1
                    
                await event.edit(f"⏳ **جاري السحب والإضافة...**\n✅ **تم سحبهم:** `{added}`\n🔸 **خصوصية / تجاهل:** `{restricted}`\n❌ **فشل / غير مسموح:** `{failed}`")
                await asyncio.sleep(3)
                
            except ChatAdminRequiredError:
                failed += 1
                await event.edit("⚠️ **المجموعة هنا تمنع الأعضاء العاديين من إضافة أفراد (تتطلب صلاحية مشرف).**")
                return
            except UserPrivacyRestrictedError:
                restricted += 1
            except Exception as e:
                failed += 1
                err_text = str(e)
                if "FLOOD" in err_text or "PeerFloodError" in err_text:
                    await event.edit(f"⚠️ **تم توقيف السحب من التليجرام (حظر مؤقت):**\n✅ تم سحب `{added}` عضو قبل التوقف.")
                    return
            
            if added >= 30:
                break

        await event.edit(f"✅ **اكتملت العملية!**\n🔹 تم سحب بنجاح: `{added}`\n🔸 قيود خصوصية / تجاهل: `{restricted}`\n❌ أخطاء أخرى: `{failed}`")

    except Exception as err:
        await event.edit(f"❌ **حدث خطأ أثناء جلب المجموعة:**\n`{err}`")

# --- م17 ---
@client.on(events.NewMessage(pattern=r"^\.م17$", outgoing=True))
async def m17(event):
    await event.edit(f"📌 **تنظيف الحسابات المغلقة (`.م17`):**\n• `.تنظيف المغلقة`\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.تنظيف المغلقة$", outgoing=True))
async def clean_deleted(event):
    if not event.is_group: return await event.edit("⚠️ للمجموعات فقط.")
    await event.edit("🔍 جاري فحص الحسابات المحذوفة...")
    users = await client.get_participants(event.chat_id)
    c = 0
    for u in users:
        if u.deleted:
            try:
                await client(EditBannedRequest(event.chat_id, u.id, ChatBannedRights(until_date=None, view_messages=True)))
                c += 1
            except: pass
    await event.edit(f"🧹 تم طرد `{c}` حساب محذوف.")

# --- م18 ---
@client.on(events.NewMessage(pattern=r"^\.م18$", outgoing=True))
async def m18(event):
    await event.edit(f"📌 **طرد البوتات (`.م18`):**\n• `.طرد البوتات`\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.طرد البوتات$", outgoing=True))
async def purge_bots(event):
    if not event.is_group: return await event.edit("⚠️ للمجموعات فقط.")
    await event.edit("🔍 جاري طرد البوتات...")
    users = await client.get_participants(event.chat_id)
    c = 0
    me = await client.get_me()
    for u in users:
        if u.bot and u.id != me.id:
            try:
                await client(EditBannedRequest(event.chat_id, u.id, ChatBannedRights(until_date=None, view_messages=True)))
                c += 1
            except: pass
    await event.edit(f"🤖 تم طرد `{c}` بوت بنجاح.")

# --- م19 ---
@client.on(events.NewMessage(pattern=r"^\.م19$", outgoing=True))
async def m19(event):
    await event.edit(f"📌 **أوامر التثبيت (`.م19`):**\n• `.تثبيت` (بالرد)\n• `.الغاء التثبيت`\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.تثبيت$", outgoing=True))
async def pin_msg(event):
    if not event.is_reply: return await event.edit("⚠️ بالرد على الرسالة.")
    r = await event.get_reply_message()
    await client.pin_message(event.chat_id, r.id)
    await event.edit("📌 تم تثبيت الرسالة بنجاح.")

@client.on(events.NewMessage(pattern=r"^\.الغاء التثبيت$", outgoing=True))
async def unpin_msg(event):
    await client.unpin_message(event.chat_id)
    await event.edit("📌 تم إلغاء تثبيت الرسالة الأخيرة.")

# --- م20 ---
@client.on(events.NewMessage(pattern=r"^\.م20$", outgoing=True))
async def m20(event):
    await event.edit(f"📌 **أوامر الإشراف والترقية (`.م20`):**\n• `.رفع مشرف` (بالرد)\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.رفع مشرف$", outgoing=True))
async def promote_user(event):
    if not event.is_reply or not event.is_group: return await event.edit("⚠️ بالرد على الرسالة في مجموعة.")
    r = await event.get_reply_message()
    rights = ChatAdminRights(
        post_messages=True, edit_messages=True, delete_messages=True,
        ban_users=True, invite_users=True, pin_messages=True, add_admins=False
    )
    await client(EditAdminRequest(event.chat_id, r.sender_id, rights, custom_title="مشرف"))
    await event.edit(f"👑 تم ترقية المستخدم: `{r.sender_id}` مشرفاً.")

# --- م21 ---
@client.on(events.NewMessage(pattern=r"^\.م21$", outgoing=True))
async def m21(event):
    await event.edit(f"📌 **أوامر الإبلاغ والسبام (`.م21`):**\n• `.بلاغ` (بالرد)\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.بلاغ$", outgoing=True))
async def report_spam(event):
    if not event.is_reply: return await event.edit("⚠️ بالرد على الرسالة المخالفة.")
    r = await event.get_reply_message()
    await client(ReportSpamRequest(peer=r.sender_id))
    await event.edit("🚨 تم رفع بلاغ سبام للتليجرام عن هذا المستخدم.")

# --- م22 ---
@client.on(events.NewMessage(pattern=r"^\.م22$", outgoing=True))
async def m22(event):
    await event.edit(f"📌 **أوامر المحادثات الخاصة (`.م22`):**\n• `.كشف الخاص`\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.كشف الخاص$", outgoing=True))
async def inspect_pms(event):
    await event.edit("🔍 جاري جلب قائمة أحدث المحادثات الخاصة...")
    dialogs = await client.get_dialogs(limit=20)
    text = "💬 **أحدث المحادثات الخاصة:**\n"
    count = 0
    for d in dialogs:
        if d.is_user and not d.entity.bot:
            count += 1
            text += f"{count}. {d.name} ➔ (`{d.id}`)\n"
            if count >= 10: break
    await event.edit(text)

# --- م23 ---
@client.on(events.NewMessage(pattern=r"^\.م23$", outgoing=True))
async def m23(event):
    await event.edit(f"📌 **صورة البروفايل (`.م23`):**\n• `.صورة البروفايل` (بالرد على صورة)\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.صورة البروفايل$", outgoing=True))
async def set_profile_photo(event):
    if not event.is_reply: return await event.edit("⚠️ يرجى الرد على الصورة.")
    r = await event.get_reply_message()
    if not r.photo: return await event.edit("⚠️ الرسالة المردود عليها ليست صورة!")
    await event.edit("⏳ جاري تعيين صورة البروفايل...")
    photo = await r.download_media()
    file = await client.upload_file(photo)
    await client(functions.photos.UploadProfilePhotoRequest(file=file))
    if os.path.exists(photo): os.remove(photo)
    await event.edit("🖼 تم تغيير صورة بروفايلك بنجاح!")

# --- م24 ---
@client.on(events.NewMessage(pattern=r"^\.م24$", outgoing=True))
async def m24(event):
    await event.edit(f"📌 **كتم المحادثات الخاصة (`.م24`):**\n• `.كتم خاص` (في الخاص أو بالرد)\n• `.فك كتم خاص`\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.كتم خاص$", outgoing=True))
async def mute_pm(event):
    target_id = None
    if event.is_private:
        target_id = event.chat_id
    elif event.is_reply:
        r = await event.get_reply_message()
        target_id = r.sender_id
    if not target_id: return await event.edit("⚠️ هذا الأمر في الخاص أو بالرد على شخص.")
    MUTED_PMS.add(target_id)
    await event.edit(f"🔇 تم كتم الشخص في الخاص: `{target_id}`")

@client.on(events.NewMessage(pattern=r"^\.فك كتم خاص$", outgoing=True))
async def unmute_pm(event):
    target_id = None
    if event.is_private:
        target_id = event.chat_id
    elif event.is_reply:
        r = await event.get_reply_message()
        target_id = r.sender_id
    if target_id in MUTED_PMS:
        MUTED_PMS.remove(target_id)
        await event.edit(f"🔊 تم فك كتم الخاص عن: `{target_id}`")
    else:
        await event.edit("⚠️ الشخص ليس مكتوماً في الخاص.")

# --- م25 ---
@client.on(events.NewMessage(pattern=r"^\.م25$", outgoing=True))
async def m25(event):
    await event.edit(f"📌 **حفظ الميديا الذاتية (`.م25`):**\n• `.حفظ` (بالرد على الصورة/الفيديو المؤقت)\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.حفظ$", outgoing=True))
async def save_self_destruct(event):
    if not event.is_reply: return await event.edit("⚠️ بالرد على الميديا المؤقتة.")
    r = await event.get_reply_message()
    if not (r.photo or r.video or r.media): return await event.edit("⚠️ الرسالة لا تحتوي وسائط!")
    await event.edit("⏳ جاري تحميل الميديا وحفظها...")
    file_path = await r.download_media()
    await client.send_file("me", file_path, caption=f"📥 **تم حفظ الوسائط بنجاح.**\n{SOURCE_TITLE}")
    if os.path.exists(file_path): os.remove(file_path)
    await event.edit("✅ **تم تحميل الميديا وإرسالها لـ الرسائل المحفوظة (Saved Messages)!**")

# --- م26 ---
@client.on(events.NewMessage(pattern=r"^\.م26$", outgoing=True))
async def m26(event):
    await event.edit(f"📌 **معرفة رتب الأعضاء (`.م26`):**\n• `.رتبتي`\n• `.رتبته` (بالرد)\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.رتبتي$", outgoing=True))
async def my_rank(event):
    if not event.is_group: return await event.edit("⚠️ داخل المجموعات فقط.")
    perms = await client.get_permissions(event.chat_id, event.sender_id)
    if perms.is_creator: rank = "👑 المالك الأساسي"
    elif perms.is_admin: rank = "🛡 مشرف في المجموعة"
    else: rank = "👤 عضو عادي"
    await event.edit(f"📊 **رتبتك في الكروب:** {rank}")

@client.on(events.NewMessage(pattern=r"^\.رتبته$", outgoing=True))
async def user_rank(event):
    if not event.is_reply or not event.is_group: return await event.edit("⚠️ بالرد داخل مجموعة.")
    r = await event.get_reply_message()
    perms = await client.get_permissions(event.chat_id, r.sender_id)
    if perms.is_creator: rank = "👑 المالك الأساسي"
    elif perms.is_admin: rank = "🛡 مشرف في المجموعة"
    else: rank = "👤 عضو عادي"
    await event.edit(f"📊 **رتبة المستخدم:** {rank}")

# --- م27 ---
@client.on(events.NewMessage(pattern=r"^\.م27$", outgoing=True))
async def m27(event):
    await event.edit(f"📌 **أوامر السورس والنظام (`.م27`):**\n• `.ريستارت` (إعادة تشغيل البوت)\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.ريستارت$", outgoing=True))
async def restart_bot(event):
    await event.edit("🔄 **جاري إعادة تشغيل السورس...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

# --- م28 ---
@client.on(events.NewMessage(pattern=r"^\.م28$", outgoing=True))
async def m28(event):
    await event.edit(f"📌 **قياس سرعة السيرفر (`.م28`):**\n• `.بنج`\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.بنج$", outgoing=True))
async def ping_cmd(event):
    start = datetime.datetime.now()
    await event.edit("🚀 **PONG!**")
    end = datetime.datetime.now()
    ms = (end - start).microseconds / 1000
    await event.edit(f"⚡ **استجابة السورس:** `{ms:.2f}ms`\n{SOURCE_TITLE}")

# --- م29 ---
@client.on(events.NewMessage(pattern=r"^\.م29$", outgoing=True))
async def m29(event):
    await event.edit(f"📌 **إحصائيات الحساب (`.م29`):**\n• `.الاحصائيات`\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.الاحصائيات$", outgoing=True))
async def user_stats(event):
    await event.edit("⏳ جاري تحليل وتجميع الإحصائيات...")
    dialogs = await client.get_dialogs()
    pms, groups, channels = 0, 0, 0
    for d in dialogs:
        if d.is_user: pms += 1
        elif d.is_group: groups += 1
        elif d.is_channel: channels += 1
    await event.edit(f"📊 **إحصائيات حسابك الشاملة:**\n💬 **المحادثات الخاصة:** `{pms}`\n👥 **المجموعات:** `{groups}`\n📢 **القنوات:** `{channels}`")

# --- م30 ---
@client.on(events.NewMessage(pattern=r"^\.م30$", outgoing=True))
async def m30(event):
    await event.edit(f"📌 **الستريك وحالة السورس (`.م30`):**\n• `.ستريك`\n\n{SOURCE_TITLE}")

@client.on(events.NewMessage(pattern=r"^\.ستريك$", outgoing=True))
async def streak_status(event):
    await event.edit(f"🔥 **وضع الستريك:** شغال بدون انقطاع ✅\n{SOURCE_TITLE}")

# ----------------------------------------------------
# 5. الحارس التلقائي (المراقبة والمعالجة الشاملة)
# ----------------------------------------------------
@client.on(events.NewMessage(incoming=True))
async def global_watcher(event):
    sender_id = event.sender_id
    if not sender_id: return

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
# 6. تشغيل الحساب
# ----------------------------------------------------
print(f"⚡ {SOURCE_TITLE} يعمل بنجاح! ⚡")
client.start()
client.run_until_disconnected()

