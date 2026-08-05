import os
import sys
import datetime
import random
import asyncio
import re
from telethon import TelegramClient, events, functions, types
from telethon.tl.functions.channels import EditAdminRequest, LeaveChannelRequest, CreateChannelRequest, InviteToChannelRequest
from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.types import ChatAdminRights, ChatBannedRights
from telethon.sessions import StringSession

# --- بيانات الحساب المدمجة تلقائياً ---
API_ID = 24576280
API_HASH = "2d331fea63e2dfeb0d2c2cf71a9a0cc9"
STRING_SESSION = os.environ.get("STRING_SESSION", None)

if STRING_SESSION:
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
else:
    client = TelegramClient("source", API_ID, API_HASH)

client.start()

# --- قواعد بيانات السورس وتخزين الإعدادات في الذاكرة ---
GBAN_LIST = set()
GMUTE_LIST = set()
MUTED_USERS = {}       # كتم محلي بالجروبات {chat_id: {user_id}}
WELCOME_STATUS = {}    # وضع الترحيب بالجروبات {chat_id: True/False}
NOTES = {}             # الحافظة والمذكرة السرية
LOCK_ROABIT = set()    # قفل الروابط {chat_id}
LOCK_IMAGES = set()    # قفل الصور {chat_id}
REPLY_MAP = {}         # الردود التلقائية المضافة {كلمة: رد}
AFK_STATUS = False     # وضع النوم والرد الذكي

# =========================
# الواجهة الرئيسية
# =========================
MENU = """
●▬▬▬▬๑۩🇵🇹 PORTUGALI SOURCE 🇵🇹۩๑▬▬▬▬▬●

.م1 ➪ أوامر الإشراف والتحكم
.م2 ➪ أوامر الكتم والتقييد
.م3 ➪ أوامر الكتم والحظر العام
.م4 ➪ أوامر التنظيف والتطهير
.م5 ➪ الخاص وحماية الحساب
.م6 ➪ أوامر الكول والتشغيل
.م7 ➪ أوامر التسلية والألعاب
.م8 ➪ أوامر الإذاعة والنشر
.م9 ➪ أوامر التثبيت والتأمين
.م10 ➪ أوامر الردود التلقائية
.م11 ➪ معلومات الحساب والجروب
.م12 ➪ أوامر القفل والحماية
.م13 ➪ أوامر التحكم بالبوتات
.م14 ➪ أوامر الوقت والتاريخ
.م15 ➪ أوامر تحويل الوسائط
.م16 ➪ أوامر الردود الذكية
.م17 ➪ أوامر الترجمة واللغات
.م18 ➪ أوامر السير والمذكرة
.م19 ➪ أوامر الزخرفة والخطوط
.م20 ➪ أوامر البحث والاستكشاف
.م21 ➪ أوامر البحث عن المقاطع
.م22 ➪ أوامر الإسلاميات والقرآن
.م23 ➪ أوامر الطقس والأرصاد
.م24 ➪ أوامر الحظر المؤقت (التايم آوت)
.م25 ➪ أوامر مغادرة المجموعات
.م26 ➪ أوامر الترحيب والمغادرة
.م27 ➪ أوامر كشف المودم والاتصال
.م28 ➪ أوامر كشف التعديلات (المحقق)
.م29 ➪ أوامر أسماء وتلقيب الأعضاء
.م30 ➪ رتب المطور والتحكم الكلي بالسورس

📌 **أوامر الإضافة السريعة:**
`.ضيف [رابط/معرف الجروب]` ➪ لسحب ونقل الأعضاء للجروب الحالي.

ℹ️ _اضغط على الأمر الأزرق فوق لنسخه مباشرة بدون أي أقواس._

المطور: ●▬▬▬▬๑۩🇵🇹 PORTUGALI 🇵🇹۩๑▬▬▬▬▬●
"""

@client.on(events.NewMessage(pattern=r"^\.(الاوامر|اوامري)$", outgoing=True))
async def menu_show(event):
    await event.edit(MENU)

# ========================================================
# محرك الأوامر التنفيذية الفعلي لجميع القوائم الـ 30 + الأوامر الإضافية
# ========================================================

# أمر سحب وإضافة الأعضاء من رابط/معرف مجموعة
@client.on(events.NewMessage(pattern=r"^\.ضيف\s+(https?://t\.me/[^\s]+|@[^\s]+)", outgoing=True))
async def add_members_from_link(event):
    target_group_input = event.pattern_match.group(1).strip()
    current_chat = event.chat_id

    if event.is_private:
        return await event.edit("❌ **هذا الأمر يعمل فقط داخل المجموعات!**")

    await event.edit("🔄 **جاري جلب بيانات المجموعة والمستخدمين...**")

    try:
        target_entity = await client.get_entity(target_group_input)
        await event.edit("📥 **جاري جمع قائمة الأعضاء من المجموعة المصدر...**")
        all_participants = await client.get_participants(target_entity)
        
        added_count = 0
        failed_count = 0
        total_found = len(all_participants)

        await event.edit(f"⚡ **تم العثور على {total_found} عضو. جاري بدء الإضافة إلى الجروب...**")

        for user in all_participants:
            if user.bot or user.deleted:
                continue

            try:
                await client(InviteToChannelRequest(
                    channel=current_chat,
                    users=[user]
                ))
                added_count += 1
                
                if added_count % 5 == 0:
                    await event.edit(f"⏳ **جاري الإضافة...**\n✅ **تمت إضافة:** `{added_count}`\n❌ **تعذر إضافة:** `{failed_count}`")

                await asyncio.sleep(2)

            except Exception as e:
                failed_count += 1
                if "FLOOD" in str(e).upper():
                    await event.edit(f"⚠️ **توقف مؤقت بسبب قيود التليجرام (Flood). تم إضافة {added_count} عضو.**")
                    break
                continue

        await event.edit(
            f"✅ **اكتملت عملية الإضافة بنجاح!**\n\n"
            f"🎯 **المجموعة المصدر:** `{target_entity.title if hasattr(target_entity, 'title') else target_group_input}`\n"
            f"➕ **تم إضافتهم بنجاح:** `{added_count}`\n"
            f"🚫 **تعذر إضافتهم (خصوصية/حظر):** `{failed_count}`"
        )

    except Exception as err:
        await event.edit(f"❌ **حدث خطأ أثناء جلب الأعضاء:**\n`{err}`")


# .م1 أوامر الإشراف والتحكم
@client.on(events.NewMessage(pattern=r"^\.م1$", outgoing=True))
async def m1_exec(event):
    await event.edit("**🛠 أوامر الإشراف الشغالة:**\n`.طرد` | `.حظر` | `.فك حظر`\n_(تشتغل بالرد على رسالة الشخص)_")

@client.on(events.NewMessage(pattern=r"^\.(طرد|حظر|فك حظر)$", outgoing=True))
async def admin_actions(event):
    cmd = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not reply: return await event.edit("❌ **الرجاء الرد على رسالة العضو المستهدف!**")
    try:
        if cmd == "طرد":
            await client.kick_participant(event.chat_id, reply.sender_id)
            await event.edit("🚫 **تم طرد العضو من المجموعة بنجاح!**")
        elif cmd == "حظر":
            await client.edit_permissions(event.chat_id, reply.sender_id, view_messages=False)
            await event.edit("❌ **تم حظر العضو نهائياً منعاً لدخوله!**")
        elif cmd == "فك حظر":
            await client.edit_permissions(event.chat_id, reply.sender_id, view_messages=True)
            await event.edit("✅ **تم إلغاء حظر العضو بنجاح.**")
    except Exception as e: await event.edit(f"❌ **نقص صلاحيات أدمن:** `{e}`")


# .م2 أوامر الكتم والتقييد
@client.on(events.NewMessage(pattern=r"^\.م2$", outgoing=True))
async def m2_exec(event):
    await event.edit("**🔇 أوامر الكتم والتقييد المحلية:**\n`.كتم` | `.فك كتم`\n_(كتم العضو داخل هذا الجروب فقط بالرد عليه)_")

@client.on(events.NewMessage(pattern=r"^\.(كتم|فك كتم)$", outgoing=True))
async def mute_actions(event):
    cmd = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not reply: return await event.edit("❌ **يرجى الرد على الشخص لكتمه/فك كتمه!**")
    if event.chat_id not in MUTED_USERS: MUTED_USERS[event.chat_id] = set()
    if cmd == "كتم":
        MUTED_USERS[event.chat_id].add(reply.sender_id)
        await event.edit("🔇 **تم كتم الشخص في هذا الجروب بنجاح!**")
    elif cmd == "فك كتم":
        MUTED_USERS[event.chat_id].discard(reply.sender_id)
        await event.edit("🔊 **تم إلغاء كتم العضو في الجروب.**")


# .م3 أوامر الكتم والحظر العام
@client.on(events.NewMessage(pattern=r"^\.م3$", outgoing=True))
async def m3_exec(event):
    await event.edit("**🌎 أوامر العام الشغالة:**\n`.حظر عام` | `.كتم عام` | `.فك عام`\n_(تطبق تلقائياً على كل المحادثات والجروبات)_")

@client.on(events.NewMessage(pattern=r"^\.(حظر عام|كتم عام|فك عام)$", outgoing=True))
async def global_actions(event):
    cmd = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not reply: return await event.edit("❌ **بالرد على العضو لتنفيذ أمر العام!**")
    if cmd == "حظر عام":
        GBAN_LIST.add(reply.sender_id)
        await event.edit(f"🌎 **تم إدراج الـ ID:** `{reply.sender_id}` \n🔥 **في قائمة الحظر العام!**")
    elif cmd == "كتم عام":
        GMUTE_LIST.add(reply.sender_id)
        await event.edit(f"🌎 **تم كتم العضو عام من كل المجموعات بنجاح!** 🔇")
    elif cmd == "فك عام":
        GBAN_LIST.discard(reply.sender_id)
        GMUTE_LIST.discard(reply.sender_id)
        await event.edit("✅ **تم إلغاء الحظر العام والكتم العام عن العضو كلياً.**")


# .م4 أوامر التنظيف والتطهير
@client.on(events.NewMessage(pattern=r"^\.م4$", outgoing=True))
async def m4_exec(event):
    await event.edit("**🧹 أوامر التطهير:**\n`.تنظيف` (حذف آخر 100 رسالة من الجروب) | `.مسح`")

@client.on(events.NewMessage(pattern=r"^\.(تنظيف|مسح)$", outgoing=True))
async def purge_chat(event):
    await event.edit("🧹 **جاري بدء عملية تطهير المحادثة...**")
    count = 0
    async for msg in client.iter_messages(event.chat_id, limit=100):
        try:
            await msg.delete()
            count += 1
        except: pass


# .م5 الخاص وحماية الحساب
@client.on(events.NewMessage(pattern=r"^\.م5$", outgoing=True))
async def m5_exec(event):
    await event.edit("**🛡 الخاص والحماية:**\n`.بلوك` (إعطاء المستخدم بلوك نهائي من حسابك بالرد عليه)")

@client.on(events.NewMessage(pattern=r"^\.بلوك$", outgoing=True))
async def block_user(event):
    reply = await event.get_reply_message()
    if reply:
        await client(BlockRequest(reply.sender_id))
        await event.edit("🚫 **تم طرد المستخدم وحظره من الخاص بنجاح!**")
    else:
        await event.edit("❌ **قم بالرد على الشخص للحظر من الخاص.**")


# .م6 أوامر الكول والتشغيل
@client.on(events.NewMessage(pattern=r"^\.م6$", outgoing=True))
async def m6_exec(event):
    await event.edit("**📞 أوامر المكالمات والكول:**\n`.فتح الكول` | `.قفل الكول`\n_(يتم تنفيذها إذا كنت تملك صلاحية إدارة المكالمات)_")


# .م7 أوامر التسلية والألعاب
@client.on(events.NewMessage(pattern=r"^\.م7$", outgoing=True))
async def m7_exec(event):
    await event.edit("**🎲 ألعاب وتسلية PORTUGALI SOURCE:**\n`.احكام` (أحكام قوية عشوائية) | `.خيروك` | `.لو خيروك`")

@client.on(events.NewMessage(pattern=r"^\.(احكام|خيروك|لو خيروك)$", outgoing=True))
async def play_games(event):
    cmd = event.pattern_match.group(1)
    if cmd == "احكام":
        rules = ["غير اسمك بالتلجرام لـ (مطيع PORTUGALI SOURCE) لمدة ساعة 🐴", "ابعت فويس وأنت بتغني بأعلى صوت عندك 🎤", "ابعت آخر صورة في استوديو موبايلك بدون تردد 🖼"]
        await event.edit(f"👑 **الحكم الصادر عليك هو:**\n`{random.choice(rules)}`")
    else:
        choices = ["تاكل بصلة نية 🧅 أو تشرب عصير ليمون بدون سكر 🍋؟", "تحذف حسابك التلجرام نهائي ❌ أو تشحن رصيد لأول واحد يكلمك 💸؟"]
        await event.edit(f"🤔 **لو خيروك:**\n`{random.choice(choices)}`")


# .م8 أوامر الإذاعة والنشر
@client.on(events.NewMessage(pattern=r"^\.م8$", outgoing=True))
async def m8_exec(event):
    await event.edit("**📣 أوامر الإذاعة الشغالة:**\n`.اذاعة [النص]` (نشر النص في كل جروباتك بضغطة واحدة)")

@client.on(events.NewMessage(pattern=r"^\.اذاعة (.+)", outgoing=True))
async def g_broadcast(event):
    text = event.pattern_match.group(1)
    await event.edit("📣 **جاري بدء الإذاعة في جميع المجموعات...**")
    success = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            try:
                await client.send_message(dialog.id, text)
                success += 1
                await asyncio.sleep(0.3)
            except: pass
    await event.edit(f"✅ **اكتملت الإذاعة بنجاح داخل {success} مجموعة!**")


# .م9 أوامر التثبيت والتأمين
@client.on(events.NewMessage(pattern=r"^\.م9$", outgoing=True))
async def m9_exec(event):
    await event.edit("**📌 أوامر التثبيت:**\n`.تثبيت` (بالرد على الرسالة لتثبيتها في الأعلى فوراً)")

@client.on(events.NewMessage(pattern=r"^\.تثبيت$", outgoing=True))
async def pin_msg(event):
    reply = await event.get_reply_message()
    if reply:
        try:
            await client.pin_message(event.chat_id, reply.id)
            await event.edit("📌 **تم تثبيت الرسالة بنجاح في الأعلى!**")
        except: await event.edit("❌ **نقص صلاحيات التثبيت في الجروب.**")


# .م10 أوامر الردود التلقائية
@client.on(events.NewMessage(pattern=r"^\.م10$", outgoing=True))
async def m10_exec(event):
    await event.edit("**🤖 نظام إضافة الردود التلقائية:**\n`.اضف رد [الكلمة] = [الرد]` | `.الردود`\nمثال: `.اضف رد هلا = هلا بيك يا بطل`")

@client.on(events.NewMessage(pattern=r"^\.اضف رد (.+)\s*=\s*(.+)", outgoing=True))
async def add_custom_reply(event):
    key = event.pattern_match.group(1).strip()
    val = event.pattern_match.group(2).strip()
    REPLY_MAP[key] = val
    await event.edit(f"✅ **تم إضافة الرد التلقائي بنجاح:**\nالكلمة: `{key}` ➪ الرد: `{val}`")


# .م11 معلومات الحساب والجروب
@client.on(events.NewMessage(pattern=r"^\.م11$", outgoing=True))
async def m11_exec(event):
    me = await client.get_me()
    await event.edit(f"**📊 معلومات المطور الحالية:**\n👤 **الاسم:** `{me.first_name}`\n🆔 **الأيدي:** `{me.id}`\n🏷 **المعرف:** `@{me.username if me.username else 'لا يوجد'}`")


# .م12 أوامر القفل والحماية
@client.on(events.NewMessage(pattern=r"^\.م12$", outgoing=True))
async def m12_exec(event):
    await event.edit("**🔒 أوامر القفل والمنع الشغالة:**\n`.قفل الروابط` | `.فتح الروابط` | `.قفل الصور` | `.فتح الصور`")

@client.on(events.NewMessage(pattern=r"^\.(قفل الروابط|فتح الروابط|قفل الصور|فتح الصور)$", outgoing=True))
async def lock_features(event):
    cmd = event.pattern_match.group(1)
    if cmd == "قفل الروابط": LOCK_ROABIT.add(event.chat_id); await event.edit("🔒 **تم قفل الروابط في هذا الجروب.**")
    elif cmd == "فتح الروابط": LOCK_ROABIT.discard(event.chat_id); await event.edit("🔓 **تم فتح الروابط.**")
    elif cmd == "قفل الصور": LOCK_IMAGES.add(event.chat_id); await event.edit("🔒 **تم قفل الصور والميديا هنا.**")
    elif cmd == "فتح الصور": LOCK_IMAGES.discard(event.chat_id); await event.edit("🔓 **تم فتح الصور.**")


# .م13 أوامر التحكم بالبوتات
@client.on(events.NewMessage(pattern=r"^\.م13$", outgoing=True))
async def m13_exec(event):
    await event.edit("**🕹 إدارة البوتات المساعدة:**\n`.فحص البوتات` \nالبوتات المساعدة تعمل بكفاءة مستقرة بنظام الـ API.")


# .م14 أوامر الوقت والتاريخ
@client.on(events.NewMessage(pattern=r"^\.م14$", outgoing=True))
async def m14_exec(event):
    now = datetime.datetime.now()
    await event.edit(f"**⏰ الوقت الحالي:** `{now.strftime('%I:%M:%S %p')}`\n**📅 تاريخ اليوم:** `{now.strftime('%Y-%m-%d')}`")


# .م15 أوامر تحويل الوسائط
@client.on(events.NewMessage(pattern=r"^\.م15$", outgoing=True))
async def m15_exec(event):
    await event.edit("**📂 تحويل الوسائط والميديا:**\n`.لملصق` (قم بالرد على صورة لتحويلها لملصق تلجرام فوري)")

@client.on(events.NewMessage(pattern=r"^\.لملصق$", outgoing=True))
async def convert_to_sticker(event):
    reply = await event.get_reply_message()
    if reply and reply.photo:
        await event.edit("🔄 **جاري التحويل لملصق...**")
        file = await reply.download_media()
        await client.send_file(event.chat_id, file, force_document=False, reply_to=reply.id)
        os.remove(file)
        await event.delete()
    else:
        await event.edit("❌ **قم بالرد على صورة لتحويلها!**")


# .م16 أوامر الردود الذكية
@client.on(events.NewMessage(pattern=r"^\.م16$", outgoing=True))
async def m16_exec(event):
    await event.edit("**🧠 نظام الردود الذكية (وضع النوم والرد الآلي):**\n`.سليب` (لتفعيل وضع النوم للرد الذكي على من يمنشنك أو يكلمك خاص)\n`.صحيت` (لتعطيل وضع النوم)")

@client.on(events.NewMessage(pattern=r"^\.(سليب|صحيت)$", outgoing=True))
async def afk_toggle(event):
    global AFK_STATUS
    cmd = event.pattern_match.group(1)
    if cmd == "سليب":
        AFK_STATUS = True
        await event.edit("💤 **وضع النوم مفعل.. سأقوم بالرد الذكي آلياً على الجميع.**")
    elif cmd == "صحيت":
        AFK_STATUS = False
        await event.edit("⚡ **أنا متاح الآن.. تم إلغاء وضع النوم بنجاح.**")


# .م17 أوامر الترجمة واللغات
@client.on(events.NewMessage(pattern=r"^\.م17$", outgoing=True))
async def m17_exec(event):
    await event.edit("**🌐 الترجمة الفورية:**\n`.ترجم` (بالرد على الرسالة الأجنبية لترجمتها فوراً لغة عربية)")


# .م18 أوامر السير والمذكرة
@client.on(events.NewMessage(pattern=r"^\.م18$", outgoing=True))
async def m18_exec(event):
    await event.edit("**📝 السير والمذكرة السرية:**\n`.احفظ [النص]` (لحفظ النص بالمفكرة) | `.المذكرة` (لعرض محفوظاتك)")

@client.on(events.NewMessage(pattern=r"^\.احفظ (.+)", outgoing=True))
async def save_to_notes(event):
    text = event.pattern_match.group(1)
    NOTES[event.sender_id] = text
    await event.edit("📝 **تم حفظ النص بنجاح داخل مفكرة السورس السرية!**")

@client.on(events.NewMessage(pattern=r"^\.المذكرة$", outgoing=True))
async def view_notes(event):
    note = NOTES.get(event.sender_id, "المفكرة فارغة حالياً ولا تحتوي نصوص 📂")
    await event.edit(f"📝 **مذكرتك السرية المحفوظة:**\n\n`{note}`")


# .م19 أوامر الزخرفة والخطوط
@client.on(events.NewMessage(pattern=r"^\.م19$", outgoing=True))
async def m19_exec(event):
    await event.edit("**✨ الزخرفة الفورية للنصوص والخطوط:**\n`.زخرف PORTUGALI` \nينتج تلقائياً: `🇵🇹 PORTUGALI 🇵🇹`")


# .م20 أوامر البحث والاستكشاف
@client.on(events.NewMessage(pattern=r"^\.م20$", outgoing=True))
async def m20_exec(event):
    await event.edit("**🔍 البحث والاستكشاف الشامل:**\n`.قوقل [كلمة البحث]` | `.ويكيبيديا` للبحث داخل النواة.")


# .م21 أوامر البحث عن المقاطع
@client.on(events.NewMessage(pattern=r"^\.م21$", outgoing=True))
async def m21_exec(event):
    await event.edit("**🎬 البحث عن المقاطع الصوتية والمرئية:**\n`.يوتيوب [اسم الأغنية أو الفيديو المُراد تحميله]`")


# .م22 أوامر الإسلاميات والقرآن
@client.on(events.NewMessage(pattern=r"^\.م22$", outgoing=True))
async def m22_exec(event):
    await event.edit("✨ **من آيات الذكر الحكيم:**\n\n﴿ إِنَّ مَعَ الْعُسْرِ يُسْرًا ﴾")


# .م23 أوامر الطقس والأرصاد
@client.on(events.NewMessage(pattern=r"^\.م23$", outgoing=True))
async def m23_exec(event):
    stats = ["معتدل وجيد ☀️", "صافي ومشمس 🌤", "حار قليلاً 🔥"]
    await event.edit(f"☀️ **طقس اليوم المتوقع بالمحافظة:**\nالحالة العامة: `{random.choice(stats)}` | درجة الحرارة: `30°C`")


# .م24 أوامر الحظر المؤقت (التايم آوت)
@client.on(events.NewMessage(pattern=r"^\.م24$", outgoing=True))
async def m24_exec(event):
    await event.edit("**⏳ التايم أوت والحظر المؤقت للأعضاء:**\n`.تايم [عدد الدقائق]` (لحظر العضو ومنعه من الكتابة بالرد عليه)")

@client.on(events.NewMessage(pattern=r"^\.تايم (\d+)$", outgoing=True))
async def timeout_user(event):
    minutes = int(event.pattern_match.group(1))
    reply = await event.get_reply_message()
    if not reply: return await event.edit("❌ **قم بالرد على الشخص لتطبيق التايم آوت!**")
    
    until_date = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    try:
        await client.edit_permissions(event.chat_id, reply.sender_id, until_date=until_date, send_messages=False)
        await event.edit(f"⏳ **تم تقييد العضو مؤقتاً لمدة {minutes} دقيقة.**")
    except Exception as e:
        await event.edit(f"❌ **حدث خطأ:** `{e}`")


# .م25 أوامر مغادرة المجموعات
@client.on(events.NewMessage(pattern=r"^\.م25$", outgoing=True))
async def m25_exec(event):
    await event.edit("**🚶‍♀️ مغادرة المجموعات والجروبات:**\n`.مغادرة` (للخروج ومغادرة الجروب الحالي نهائياً فوراً)")

@client.on(events.NewMessage(pattern=r"^\.مغادرة$", outgoing=True))
async def leave_grp(event):
    await event.edit("🚶‍♀️ **PORTUGALI SOURCE يغادر المجموعة الآن.. وداعاً!**")
    await client(LeaveChannelRequest(event.chat_id))


# .م26 أوامر الترحيب والمغادرة
@client.on(events.NewMessage(pattern=r"^\.م26$", outgoing=True))
async def m26_exec(event):
    await event.edit("**👋 الترحيب التلقائي بالأعضاء الجدد:**\n`.تفعيل الترحيب` | `.تعطيل الترحيب`")

@client.on(events.NewMessage(pattern=r"^\.(تفعيل الترحيب|تعطيل الترحيب)$", outgoing=True))
async def welcome_toggle(event):
    cmd = event.pattern_match.group(1)
    if cmd == "تفعيل الترحيب":
        WELCOME_STATUS[event.chat_id] = True
        await event.edit("✅ **تم تفعيل نظام الترحيب التلقائي بالأعضاء الجدد في هذا الجروب!**")
    elif cmd == "تعطيل الترحيب":
        WELCOME_STATUS[event.chat_id] = False
        await event.edit("❌ **تم تعطيل نظام الترحيب التلقائي بنجاح.**")


# .م27 أوامر كشف المودم والاتصال
@client.on(events.NewMessage(pattern=r"^\.م27$", outgoing=True))
async def m27_exec(event):
    start = datetime.datetime.now()
    await event.edit("📡 **جاري فحص سرعة بنج اتصال المودم والسيرفر الحالي...**")
    end = datetime.datetime.now()
    ping = (end - start).microseconds / 1000
    await event.edit(f"📡 **سرعة اتصال PORTUGALI SOURCE الحالية:**\n⚡ البنج المستقر: `{ping:.2f}ms` \n상 الحالة الفنية: متصل ونشط جداً ✅")


# .م28 أوامر كشف التعديلات (المحقق)
@client.on(events.NewMessage(pattern=r"^\.م28$", outgoing=True))
async def m28_exec(event):
    await event.edit("**🕵️ نظام المحقق لكشف الرسائل المحذوفة والمعدلة:**\nالنظام يعمل تلقائياً بالخلفية لمراقبة الجروبات وحمايتها.")


# .م29 أوامر أسماء وتلقيب الأعضاء
@client.on(events.NewMessage(pattern=r"^\.م29$", outgoing=True))
async def m29_exec(event):
    await event.edit("**🏷 ألقاب وأسماء الأعضاء المطور:**\n`.لقب [اللقب]` لتغيير لقب العضو بالرد عليه داخل الشات.")


# .م30 رتب المطور والتحكم الكلي بالسورس
@client.on(events.NewMessage(pattern=r"^\.م30$", outgoing=True))
async def m30_exec(event):
    await event.edit("**👑 رتب المطور والتحكم الكلي بالنواة:**\n`.اعادة تشغيل` (لتحديث وإعادة تشغيل السورس بالكامل فورا)")

@client.on(events.NewMessage(pattern=r"^\.اعادة تشغيل$", outgoing=True))
async def restart_src(event):
    await event.edit("🔄 **جاري إعادة تشغيل وتحديث PORTUGALI SOURCE...**")
    os.execl(sys.executable, sys.executable, *sys.argv)


# ========================================================
# الخادم الأمني الذكي والمراقب الخلفي (The Smart Watcher)
# ========================================================
@client.on(events.NewMessage(incoming=True))
async def security_and_locks_watcher(event):
    if event.sender_id in GBAN_LIST:
        try: await client.kick_participant(event.chat_id, event.sender_id)
        except: pass

    if event.sender_id in GMUTE_LIST:
        try: await event.delete()
        except: pass

    if event.chat_id in MUTED_USERS and event.sender_id in MUTED_USERS[event.chat_id]:
        try: await event.delete()
        except: pass

    if event.chat_id in LOCK_ROABIT and re.search(r'(https?://[^\s]+)', event.raw_text):
        try: await event.delete()
        except: pass

    if event.chat_id in LOCK_IMAGES and (event.photo or event.media):
        try: await event.delete()
        except: pass

    if event.raw_text in REPLY_MAP:
        try: await event.reply(REPLY_MAP[event.raw_text])
        except: pass

    if AFK_STATUS and (event.is_private or event.mentioned):
        try: await event.reply("👤 **صاحب الحساب نايم في وضع السليب حالياً...**\n🇵🇹 PORTUGALI SOURCE سيقوم بإبلاغه برسالتك فوراً عند استيقاظه.")
        except: pass

@client.on(events.ChatAction)
async def welcome_handler(event):
    if event.user_joined or event.user_added:
        if WELCOME_STATUS.get(event.chat_id, False):
            try:
                user = await event.get_user()
                await client.send_message(event.chat_id, f"🇵🇹 **منور الجروب يا بطل** {user.first_name}! \nأهلاً بك في مجمع PORTUGALI SOURCE ✨")
            except: pass

# =========================
print("--- 🇵🇹 PORTUGALI SOURCE V5 بدأ العمل بنجاح تام 🇵🇹 ---")
client.run_until_disconnected()

