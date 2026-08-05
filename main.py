import os
import sys
import asyncio
import datetime
import random
import re
from telethon import TelegramClient, events, functions, types
from telethon.tl.functions.channels import (
    EditBannedRequest, InviteToChannelRequest, GetParticipantsRequest,
    LeaveChannelRequest, CreateChannelRequest
)
from telethon.tl.functions.messages import DeleteMessagesRequest, ExportChatInviteRequest
from telethon.tl.types import ChatBannedRights
from telethon.sessions import StringSession

# ----------------------------------------------------
# 1. إعدادات الجلسة والحساب
# ----------------------------------------------------
API_ID = 24576280
API_HASH = "2d331fea63e2dfeb0d2c2cf71a9a0cc9"
STRING_SESSION = "1BJWap1wBu6wTWUI6KGHqA-rltuId7offBYF9yOSPs4eJYlvYFznWk_-xAkKxb3jHUecIxUaObuXYs4HPpfOiE45pYlIGmNToeZtpy8K6OhNW26h-HbG3MGhir-yrRgb8bufvixbF-XZ8lBkyJZ0OOahRl9l3SUYQhDdzptbTrSy2I4LDOvt96bu4yEV64owrtHKlE1KneUkdaKdhP7wM-1nAjOLvn1EbaUKGyEVfblvq2CBA-WepXGSzqa6Qvp0sG0bf0cPEZOcLPXM1NZEvRxrbcBuuh4u9bf-NGQtJaD6_S_3pb-9JVvcNl2wJjcGnfc5lV33XDmSKSA7iOfq3PujNg1oxX0E="

client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH)

SOURCE_TITLE = "🇵🇹 PORTUGALI SOURCE 🇵🇹"

# ----------------------------------------------------
# 2. الذاكرة والمصفوفات
# ----------------------------------------------------
GBAN_SET = set()
GMUTE_SET = set()
MUTED_USERS = {}
REPLY_MAP = {}
BLOCKED_WORDS = set()

GAME_ACTIVE = False
GAME_PLAYERS = []
GAME_CHAT_ID = None

# ----------------------------------------------------
# 3. القائمة الرئيسية (.الاوامر)
# ----------------------------------------------------
MAIN_MENU = f"""✦─────『 {SOURCE_TITLE} 』─────✦

.م1 ➪ أوامر البحث والوسائط
.م2 ➪ أوامر الوقت والتاريخ
.م3 ➪ أوامر إدارة المجموعات
.م4 ➪ أوامر الردود التلقائية
.م5 ➪ أوامر المسح والتنظيف
.م6 ➪ أوامر لعبة الأحكام الجماعية
.م7 ➪ أوامر كشف الحساب والآيدي
.م8 ➪ أوامر الحظر العام والفك
.م9 ➪ أوامر الكتم العام والفك
.م10 ➪ أوامر فحص ورابط المحادثة
.م11 ➪ أوامر تغيير وتحديث الاسم
.م12 ➪ أوامر البايو والبروفايل
.م13 ➪ أوامر حظر الكلمات والألفاظ
.م14 ➪ أوامر مغادرة وانضمام الكروبات
.م15 ➪ أوامر إنشاء المجموعات والقنوات
.م16 ➪ أوامر سحب وإضافة الأعضاء
.م17 ➪ أوامر تنظيف الحسابات المغلقة
.م18 ➪ أوامر طرد وحظر البوتات
.م19 ➪ أوامر التثبيت والإلغاء
.م20 ➪ أوامر نقل الملكية والإشراف
.م21 ➪ أوامر الإبلاغ والسبام
.م22 ➪ أوامر المحادثات الخاصة
.م23 ➪ أوامر صورة البروفايل
.م24 ➪ أوامر كتم الخاص
.م25 ➪ أوامر حفظ الميديا الذاتية
.م26 ➪ أوامر رتب الأعضاء
.م27 ➪ أوامر إعادة تشغيل السورس
.م28 ➪ أوامر فحص سرعة السيرفر
.م29 ➪ أوامر الإحصائيات الشاملة
"""

@client.on(events.NewMessage(pattern=r"^\.الاوامر$", outgoing=True))
async def show_main_menu(event):
    await event.edit(MAIN_MENU)

# ----------------------------------------------------
# 4. الأوامر
# ----------------------------------------------------
@client.on(events.NewMessage(pattern=r"^\.م1$", outgoing=True))
async def m1(event):
    await event.edit("📌 **أوامر البحث والوسائط (.م1):**\n• `.صورة` [اسم البحث]\n• `.بحث` [نص البحث]")

@client.on(events.NewMessage(pattern=r"^\.بحث\s+(.+)", outgoing=True))
async def search_cmd(event):
    query = event.pattern_match.group(1)
    await event.edit(f"🔍 **جاري البحث عن:** `{query}`\n🔗 https://www.google.com/search?q={query.replace(' ', '+')}")

@client.on(events.NewMessage(pattern=r"^\.م2$", outgoing=True))
async def m2(event):
    await event.edit("📌 **أوامر الوقت والتاريخ (.م2):**\n• `.الوقت`\n• `.التاريخ`")

@client.on(events.NewMessage(pattern=r"^\.الوقت$", outgoing=True))
async def get_time(event):
    t = datetime.datetime.now().strftime("%I:%M:%S %p")
    await event.edit(f"⏰ **الوقت الحالي:** `{t}`")

@client.on(events.NewMessage(pattern=r"^\.التاريخ$", outgoing=True))
async def get_date(event):
    d = datetime.datetime.now().strftime("%Y-%m-%d")
    await event.edit(f"📅 **التاريخ الحالي:** `{d}`")

@client.on(events.NewMessage(pattern=r"^\.م3$", outgoing=True))
async def m3(event):
    await event.edit("📌 **أوامر إدارة المجموعات (.م3):**\n• `.حظر` (بالرد)\n• `.فك حظر` (بالرد)\n• `.كتم` (بالرد)\n• `.فك كتم` (بالرد)")

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

@client.on(events.NewMessage(pattern=r"^\.م4$", outgoing=True))
async def m4(event):
    await event.edit("📌 **أوامر الردود التلقائية (.م4):**\n• `.رد` [الكلمة] = [الرد]\n• `.مسح الردود`")

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

@client.on(events.NewMessage(pattern=r"^\.م5$", outgoing=True))
async def m5(event):
    await event.edit("📌 **أوامر المسح والتنظيف (.م5):**\n• `.مسح` [العدد]")

@client.on(events.NewMessage(pattern=r"^\.مسح\s+(\d+)$", outgoing=True))
async def purge_messages(event):
    num = int(event.pattern_match.group(1))
    await event.delete()
    msgs = await client.get_messages(event.chat_id, limit=num)
    await client.delete_messages(event.chat_id, msgs)

@client.on(events.NewMessage(pattern=r"^\.م6$", outgoing=True))
async def m6(event):
    await event.edit(
        "📌 **أوامر لعبة الأحكام الجماعية (.م6):**\n\n"
        "• `.احكام` ➪ فتح باب الانضمام للعبة\n"
        "• `.لعب` ➪ انضمام الأعضاء للعبة (حتى 10 أعضاء)\n"
        "• `.بدء` ➪ اختيار الحاكم والمحكوم عليه عشوائياً\n"
        "• `.انهاء` ➪ إغلاق اللعبة وإعادة ضبط القائمة"
    )

@client.on(events.NewMessage(pattern=r"^\.احكام$", outgoing=True))
async def start_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not event.is_group:
        return await event.edit("⚠️ هذا الأمر يعمل داخل المجموعات فقط!")
    GAME_ACTIVE = True
    GAME_PLAYERS = []
    GAME_CHAT_ID = event.chat_id
    await event.edit(
        "🎲 **تم فتح باب الانضمام للعبة الأحكام!**\n\n"
        "👈 أرسل `.لعب` للانضمام في اللعبة (الحد الأقصى 10 أعضاء)\n"
        "⚙️ عند الاكتفاء أو الانتهاء اكتب `.بدء` لبدء القرعة عشوائياً."
    )

@client.on(events.NewMessage(pattern=r"^\.لعب$", incoming=True))
async def join_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not GAME_ACTIVE or event.chat_id != GAME_CHAT_ID:
        return
    sender = await event.get_sender()
    user_id = sender.id
    first_name = sender.first_name or "عضو"
    if any(p['id'] == user_id for p in GAME_PLAYERS):
        return await event.reply("⚠️ أنت منضم للعبة بالفعل!")
    if len(GAME_PLAYERS) >= 10:
        return await event.reply("❌ اكتمل العدد الأقصى للاعبين (10 أعضاء)!")
    GAME_PLAYERS.append({'id': user_id, 'name': first_name})
    await event.reply(f"✅ تم انضمام **[{first_name}](tg://user?id={user_id})** بنجاح! ({len(GAME_PLAYERS)}/10)")

@client.on(events.NewMessage(pattern=r"^\.بدء$", outgoing=True))
async def draw_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    if not GAME_ACTIVE or event.chat_id != GAME_CHAT_ID:
        return await event.edit("⚠️ لم تقم ببدء لعبة أحكام بعد! اكتب `.احكام` أولاً.")
    if len(GAME_PLAYERS) < 2:
        return await event.edit(f"⚠️ يجب انضمام شخصين على الأقل لبدء القرعة! (العدد الحالي: {len(GAME_PLAYERS)})")
    chosen = random.sample(GAME_PLAYERS, 2)
    hakim, mahkoum = chosen[0], chosen[1]
    await event.edit(
        f"🎯 **نتائج القرعة للجولة الحالية:**\n\n"
        f"👑 **الحاكم:** [{hakim['name']}](tg://user?id={hakim['id']})\n"
        f"⚖️ **المحكوم عليه:** [{mahkoum['name']}](tg://user?id={mahkoum['id']})\n\n"
        f"👉 يا [{hakim['name']}](tg://user?id={hakim['id']}) أحكم على [{mahkoum['name']}](tg://user?id={mahkoum['id']})!\n"
        f"🔁 عند الانتهاء اكتب `.بدء` مرة أخرى لجولة جديدة."
    )

@client.on(events.NewMessage(pattern=r"^\.انهاء$", outgoing=True))
async def stop_ahkam_game(event):
    global GAME_ACTIVE, GAME_PLAYERS, GAME_CHAT_ID
    GAME_ACTIVE = False
    GAME_PLAYERS = []
    GAME_CHAT_ID = None
    await event.edit("🔴 **تم إنهاء لعبة الأحكام وإعادة ضبط القائمة.**")

@client.on(events.NewMessage(pattern=r"^\.م7$", outgoing=True))
async def m7(event):
    await event.edit("📌 **أوامر كشف الحساب والآيدي (.م7):**\n• `.ايدي`\n• `.فحص` (بالرد)")

@client.on(events.NewMessage(pattern=r"^\.ايدي$", outgoing=True))
async def get_id(event):
    if event.is_reply:
        r = await event.get_reply_message()
        await event.edit(f"🆔 **آيدي المستخدم:** `{r.sender_id}`")
    else:
        await event.edit(f"🆔 **آيديك:** `{event.sender_id}`\n💬 **آيدي الشات:** `{event.chat_id}`")

@client.on(events.NewMessage(pattern=r"^\.فحص$", outgoing=True))
async def inspect_user(event):
    if not event.is_reply:
        return await event.edit("⚠️ يرجى الرد على المستخدم لتفحصه.")
    r = await event.get_reply_message()
    u = await client.get_entity(r.sender_id)
    await event.edit(f"👤 **الاسم:** {u.first_name}\n🆔 **الآيدي:** `{u.id}`\n🌐 **اليوزر:** @{u.username if u.username else 'لا يوجد'}")

@client.on(events.NewMessage(pattern=r"^\.م8$", outgoing=True))
async def m8(event):
    await event.edit("📌 **أوامر الحظر العام (.م8):**\n• `.حظر عام` (بالرد)\n• `.الغاء العام` (بالرد)")

@client.on(events.NewMessage(pattern=r"^\.حظر عام$", outgoing=True))
async def gban_user(event):
    if not event.is_reply:
        return await event.edit("⚠️ يرجى الرد على الشخص.")
    r = await event.get_reply_message()
    GBAN_SET.add(r.sender_id)
    await event.edit(f"🚫 تم حظر المستخدم عاماً: `{r.sender_id}`")

@client.on(events.NewMessage(pattern=r"^\.الغاء العام$", outgoing=True))
async def ungban_user(event):
    if not event.is_reply:
        return await event.edit("⚠️ يرجى الرد على الشخص.")
    r = await event.get_reply_message()
    if r.sender_id in GBAN_SET:
        GBAN_SET.remove(r.sender_id)
        await event.edit(f"✅ تم إلغاء الحظر العام عن: `{r.sender_id}`")
    else:
        await event.edit("⚠️ المستخدم غير محظور عاماً.")

@client.on(events.NewMessage(pattern=r"^\.م9$", outgoing=True))
async def m9(event):
    await event.edit("📌 **أوامر الكتم العام (.م9):**\n• `.كتم عام` (بالرد)\n• `.الغاء كتم عام` (بالرد)")

@client.on(events.NewMessage(pattern=r"^\.كتم عام$", outgoing=True))
async def gmute_user(event):
    if not event.is_reply:
        return await event.edit("⚠️ يرجى الرد على الشخص.")
    r = await event.get_reply_message()
    GMUTE_SET.add(r.sender_id)
    await event.edit(f"🔇 تم كتم المستخدم عاماً: `{r.sender_id}`")

@client.on(events.NewMessage(pattern=r"^\.الغاء كتم عام$", outgoing=True))
async def ungmute_user(event):
    if not event.is_reply:
        return await event.edit("⚠️ يرجى الرد على الشخص.")
    r = await event.get_reply_message()
    if r.sender_id in GMUTE_SET:
        GMUTE_SET.remove(r.sender_id)
        await event.edit(f"🔊 تم إلغاء الكتم العام عن: `{r.sender_id}`")
    else:
        await event.edit("⚠️ المستخدم غير مكتوم عاماً.")

@client.on(events.NewMessage(pattern=r"^\.م10$", outgoing=True))
async def m10(event):
    await event.edit("📌 **أوامر فحص الكروب والقنوات (.م10):**\n• `.الرابط` (يجلب رابط المجموعة)")

@client.on(events.NewMessage(pattern=r"^\.الرابط$", outgoing=True))
async def get_link(event):
    try:
        link = await client(ExportChatInviteRequest(event.chat_id))
        await event.edit(f"🔗 **رابط المحادثة:** {link.link}")
    except Exception as e:
        await event.edit(f"❌ لم أستطع جلب الرابط: {e}")

@client.on(events.NewMessage(pattern=r"^\.م11$", outgoing=True))
async def m11(event):
    await event.edit("📌 **أوامر تغيير الاسم (.م11):**\n• `.اسم` [الاسم الجديد]")

@client.on(events.NewMessage(pattern=r"^\.اسم\s+(.+)", outgoing=True))
async def update_name(event):
    name = event.pattern_match.group(1)
    await client(functions.account.UpdateProfileRequest(first_name=name))
    await event.edit(f"✅ تم تحديث الاسم إلى: `{name}`")

@client.on(events.NewMessage(pattern=r"^\.م12$", outgoing=True))
async def m12(event):
    await event.edit("📌 **أوامر البايو والبروفايل (.م12):**\n• `.بايو` [البايو الجديد]")

@client.on(events.NewMessage(pattern=r"^\.بايو\s+(.+)", outgoing=True))
async def update_bio(event):
    bio = event.pattern_match.group(1)
    await client(functions.account.UpdateProfileRequest(about=bio))
    await event.edit(f"✅ تم تحديث البايو إلى:\n`{bio}`")

@client.on(events.NewMessage(pattern=r"^\.م13$", outgoing=True))
async def m13(event):
    await event.edit("📌 **أوامر حظر الكلمات (.م13):**\n• `.منع` [الكلمة]\n• `.قائمة المنع`")

@client.on(events.NewMessage(pattern=r"^\.منع\s+(.+)", outgoing=True))
async def block_word(event):
    word = event.pattern_match.group(1).strip()
    BLOCKED_WORDS.add(word)
    await event.edit(f"🚫 تم إضافة الكلمة لمصفوفة المنع: `{word}`")

@client.on(events.NewMessage(pattern=r"^\.قائمة المنع$", outgoing=True))
async def list_blocked(event):
    if not BLOCKED_WORDS:
        return await event.edit("⚠️ لا توجد كلمات ممنوعة حالياً.")
    words = "\n".join([f"• `{w}`" for w in BLOCKED_WORDS])
    await event.edit(f"📜 **الكلمات الممنوعة:**\n{words}")

@client.on(events.NewMessage(pattern=r"^\.م14$", outgoing=True))
async def m14(event):
    await event.edit("📌 **أوامر المغادرة والانضمام (.م14):**\n• `.مغادرة`\n• `.انضمام` [رابط المحادثة]")

@client.on(events.NewMessage(pattern=r"^\.مغادرة$", outgoing=True))
async def leave_chat(event):
    await event.edit("👋 جاري المغادرة...")
    await client(LeaveChannelRequest(event.chat_id))

@client.on(events.NewMessage(pattern=r"^\.م15$", outgoing=True))
async def m15(event):
    await event.edit("📌 **أوامر إنشاء الكروبات والقنوات (.م15):**\n• `.انشاء كروب` [الاسم]")

@client.on(events.NewMessage(pattern=r"^\.انشاء كروب\s+(.+)", outgoing=True))
async def create_group(event):
    title = event.pattern_match.group(1)
    await client(CreateChannelRequest(title=title, about="تم إنشاؤه عبر السورس", megagroup=True))
    await event.edit(f"✅ تم إنشاء المجموعة بنجاح: `{title}`")

@client.on(events.NewMessage(pattern=r"^\.م16$", outgoing=True))
async def m16(event):
    await event.edit("📌 **أوامر إضافة الأعضاء (.م16):**\n• `.ضيف` [رابط الكروب]")

@client.on(events.NewMessage(pattern=r"^\.ضيف\s+(https?://t\.me/[^\s]+|@[^\s]+)", outgoing=True))
async def add_members(event):
    target = event.pattern_match.group(1).strip()
    if event.is_private:
        return await event.edit("⚠️ يعمل في المجموعات فقط.")
    await event.edit("⏳ جاري إضافة الأعضاء...")
    try:
        entity = await client.get_entity(target)
        users = await client.get_participants(entity)
        added = 0
        for u in users:
            if u.bot or u.deleted: continue
            try:
                await client(InviteToChannelRequest(channel=event.chat_id, users=[u]))
                added += 1
                await asyncio.sleep(2)
            except: pass
            if added >= 30: break
        await event.edit(f"✅ تم إضافة `{added}` عضو بنجاح.")
    except Exception as err:
        await event.edit(f"❌ حدث خطأ: {err}")

@client.on(events.NewMessage(pattern=r"^\.م17$", outgoing=True))
async def m17(event):
    await event.edit("📌 **تنظيف الحسابات المغلقة (.م17):**\n• `.تنظيف المغلقة`")

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

@client.on(events.NewMessage(pattern=r"^\.م18$", outgoing=True))
async def m18(event):
    await event.edit("📌 **حظر البوتات (.م18):**\n• `.طرد البوتات`")

@client.on(events.NewMessage(pattern=r"^\.طرد البوتات$", outgoing=True))
async def kick_bots(event):
    if not event.is_group: return await event.edit("⚠️ للمجموعات فقط.")
    await event.edit("🔍 جاري فحص البوتات...")
    users = await client.get_participants(event.chat_id)
    c = 0
    me = await client.get_me()
    for u in users:
        if u.bot and u.id != me.id:
            try:
                await client(EditBannedRequest(event.chat_id, u.id, ChatBannedRights(until_date=None, view_messages=True)))
                c += 1
            except: pass
    await event.edit(f"🤖 تم طرد `{c}` بوت من المجموعة.")

@client.on(events.NewMessage(pattern=r"^\.م19$", outgoing=True))
async def m19(event):
    await event.edit("📌 **أوامر التثبيت (.م19):**\n• `.تثبيت` (بالرد)\n• `.الغاء التثبيت`")

@client.on(events.NewMessage(pattern=r"^\.تثبيت$", outgoing=True))
async def pin_msg(event):
    if not event.is_reply: return await event.edit("⚠️ يرجى الرد على الرسالة المراد تثبيتها.")
    r = await event.get_reply_message()
    await client.pin_message(event.chat_id, r.id)
    await event.edit("📌 تم تثبيت الرسالة بنجاح.")

@client.on(events.NewMessage(pattern=r"^\.الغاء التثبيت$", outgoing=True))
async def unpin_msg(event):
    await client.unpin_message(event.chat_id)
    await event.edit("📌 تم إلغاء تثبيت الرسالة الأخيرة.")

@client.on(events.NewMessage(pattern=r"^\.م20$", outgoing=True))
async def m20(event): await event.edit("📌 **أوامر نقل الإشراف (.م20):**\n• `.رفع مشرف` (بالرد)")

@client.on(events.NewMessage(pattern=r"^\.م21$", outgoing=True))
async def m21(event): await event.edit("📌 **أوامر الإبلاغ والسبام (.م21):**\n• `.بلاغ` (بالرد)")

@client.on(events.NewMessage(pattern=r"^\.م22$", outgoing=True))
async def m22(event): await event.edit("📌 **أوامر المحادثات الخاص (.م22):**\n• `.كشف الخاص`")

@client.on(events.NewMessage(pattern=r"^\.م23$", outgoing=True))
async def m23(event): await event.edit("📌 **أوامر صورة البروفايل (.م23):**\n• `.صورة البروفايل` (بالرد على صورة)")

@client.on(events.NewMessage(pattern=r"^\.م24$", outgoing=True))
async def m24(event): await event.edit("📌 **أوامر كتم الخاص (.م24):**\n• `.كتم خاص` (بالرد)")

@client.on(events.NewMessage(pattern=r"^\.م25$", outgoing=True))
async def m25(event): await event.edit("📌 **حفظ الميديا الذاتية (.م25):**\n• `.حفظ` (بالرد على ميديا مؤقتة)")

@client.on(events.NewMessage(pattern=r"^\.حفظ$", outgoing=True))
async def save_media(event):
    if not event.is_reply:
        return await event.edit("⚠️ يرجى الرد على الوسائط المحددة بوقت.")
    r = await event.get_reply_message()
    if r.media:
        path = await r.download_media()
        await client.send_file("me", path, caption="📁 تم حفظ الوسائط الذاتية بنجاح.")
        os.remove(path)
        await event.edit("✅ تم حفظ الصورة/الفيديو في المحفوظات الخاص بك.")
    else:
        await event.edit("⚠️ الرسالة لا تحتوي على وسائط.")

@client.on(events.NewMessage(pattern=r"^\.م26$", outgoing=True))
async def m26(event): await event.edit("📌 **أوامر رتب الأعضاء (.م26):**\n• `.رتبتي`\n• `.رتبته` (بالرد)")

@client.on(events.NewMessage(pattern=r"^\.رتبتي$", outgoing=True))
async def my_rank(event):
    if event.is_private: return await event.edit("👤 أنت المالك الحقيقي للحساب.")
    p = await client.get_permissions(event.chat_id, event.sender_id)
    if p.is_creator: await event.edit("👑 أنت منشئ المجموعة (المالك).")
    elif p.is_admin: await event.edit("⭐ أنت مشرف في هذه المجموعة.")
    else: await event.edit("👤 أنت عضو عادي في المجموعة.")

@client.on(events.NewMessage(pattern=r"^\.م27$", outgoing=True))
async def m27(event): await event.edit("📌 **إعادة تشغيل السورس (.م27):**\n• `.ريستارت`")

@client.on(events.NewMessage(pattern=r"^\.ريستارت$", outgoing=True))
async def restart_script(event):
    await event.edit("🔄 جاري إعادة تشغيل السورس...")
    os.execl(sys.executable, sys.executable, *sys.argv)

@client.on(events.NewMessage(pattern=r"^\.م28$", outgoing=True))
async def m28(event): await event.edit("📌 **فحص السرعة (.م28):**\n• `.بنج`")

@client.on(events.NewMessage(pattern=r"^\.بنج$", outgoing=True))
async def ping_cmd(event):
    start = datetime.datetime.now()
    await event.edit("⚡ **Pong!**")
    end = datetime.datetime.now()
    ms = (end - start).microseconds / 1000
    await event.edit(f"⚡ **سرعة استجابة السورس:** `{ms}ms`")

@client.on(events.NewMessage(pattern=r"^\.م29$", outgoing=True))
async def m29(event): await event.edit("📌 **الإحصائيات الشاملة (.م29):**\n• `.الاحصائيات`")

@client.on(events.NewMessage(pattern=r"^\.الاحصائيات$", outgoing=True))
async def get_stats(event):
    dialogs = await client.get_dialogs()
    chats = sum(1 for d in dialogs if d.is_group)
    users = sum(1 for d in dialogs if d.is_user)
    channels = sum(1 for d in dialogs if d.is_channel and not d.is_group)
    await event.edit(f"📊 **إحصائيات الحساب والسورس:**\n\n👥 **المجموعات:** `{chats}`\n👤 **المحادثات الخاصة:** `{users}`\n📢 **القنوات:** `{channels}`")

# ----------------------------------------------------
# 5. الحارس العام (Watcher)
# ----------------------------------------------------
@client.on(events.NewMessage(incoming=True))
async def global_watcher(event):
    sender = event.sender_id
    if sender in GBAN_SET or sender in GMUTE_SET:
        try: await event.delete()
        except: pass
        return
    if event.chat_id in MUTED_USERS and sender in MUTED_USERS[event.chat_id]:
        try: await event.delete()
        except: pass
        return
    if BLOCKED_WORDS:
        for w in BLOCKED_WORDS:
            if w in event.raw_text:
                try: await event.delete()
                except: pass
                return
    if event.raw_text in REPLY_MAP:
        try: await event.reply(REPLY_MAP[event.raw_text])
        except: pass

# ----------------------------------------------------
# 6. التشغيل الأكيد بدون استدعاء input()
# ----------------------------------------------------
async def main():
    await client.connect()
    if not await client.is_user_authorized():
        print("❌ الـ String Session غير صالحة أو تم إلغاؤها من تليجرام!")
        return

    print(f"=== {SOURCE_TITLE} IS RUNNING SUCCESSFULLY ===")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())

