import asyncio
from datetime import datetime

from telethon.errors import BadRequestError, FloodWaitError, ForbiddenError

from userbot import november

from ..Config import Config
from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply
from ..helpers import reply_id, time_formatter
from ..helpers.utils import _format
from ..sql_helper.bot_blacklists import check_is_black_list, get_all_bl_users
from ..sql_helper.bot_starters import del_starter_from_db, get_all_starters
from ..sql_helper.globals import addgvar, delgvar, gvarstatus
from . import BOTLOG, BOTLOG_CHATID
from .botmanagers import (
    ban_user_from_bot,
    get_user_and_reason,
    progress_str,
    unban_user_from_bot,
)

LOGS = logging.getLogger(__name__)

plugin_category = "bot"
botusername = Config.TG_BOT_USERNAME
cmhd = Config.COMMAND_HAND_LER


@november.nov_cmd(
    pattern=f"^اوامري$",
    from_users=Config.OWNER_ID,
)
async def bot_help(event):
    await event.reply(
        f"**▾∮ قائـمه اوامر المطور ↶**\n* `تستخدم في ↫ `{botusername} ` فقط! `\n\n/info\n**▾∮قم بالرد ع المستخدم لجلب معلوماتة ↶**\n*`لمعرفة الملصقات المرسلة` ツ\n/ban\n**▾∮قم بالرد ع المستخدم واعطاؤه السبب او ↶**\n**/ban @nneee + السبب**\n*` لحظر المستخدم من البوت `✘\n/unban\n**▾∮الامر والمعرف والسبب (اختياري) ↶**\n**/unban @nneee + السبب اختياري**\n* `لالغاء حظر المستخدم من البوت `√\n/banlist \n**▾∮لمعرفة المحظورين من البوت ㋡**\n/antif + on & off\n**▾∮لتشغيل وايقاف التكرار ↶**\n* `عند التشغيل يحظر المزعجين `⊝\n/cast\n**▾∮قم بالرد ع الرسالة لاذاعتها للمستخدمين ↸**\n* `لنشر رسالة لمستخدمي البوت `◛\n\n**⍣ⵧⵧⵧⵧⵧɴᴏᴠᴇᴍʙᴇʀⵧⵧⵧⵧⵧ⍣**\n[▾∮ՏøuƦcε πøνεʍβεƦ 🌦](https://t.me/nneee)"
    )
@november.nov_cmd(
    pattern=f"^/cast$",
    from_users=Config.OWNER_ID,
)
async def bot_broadcast(event):
    replied = await event.get_reply_message()
    if not replied:
        return await event.reply("**▾∮قم بالرد ع الرسالة لاذاعتها اولًا! 📫**")
    start_ = datetime.now()
    br_cast = await replied.reply("**▾∮جاري تحضير الرسالة لايذاعها! 📬**")
    blocked_users = []
    count = 0
    bot_users_count = len(get_all_starters())
    if bot_users_count == 0:
        return await event.reply("**▾∮ليس لديك مستخدمين في بوتك!⚠️ **")
    users = get_all_starters()
    if users is None:
        return await event.reply("**▾∮لم يستطيع جلب قائمة للمستخدمين ✘ **")
    for user in users:
        try:
            await event.client.send_message(
                int(user.user_id), "**▾∮عزيزي تسلمت رسالة جديدة 📢 **"
            )
            await event.client.send_message(int(user.user_id), replied)
            await asyncio.sleep(0.8)
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except (BadRequestError, ValueError, ForbiddenError):
            del_starter_from_db(int(user.user_id))
        except Exception as e:
            LOGS.error(str(e))
            if BOTLOG:
                await event.client.send_message(
                    BOTLOG_CHATID, f"**▾∮حصل خطأ عند اذاعة رسالتك ✘ **\n`{str(e)}`"
                )
        else:
            count += 1
            if count % 5 == 0:
                try:
                    prog_ = (
                        "**▾∮جاري تحضير الرسالة لايذاعها! 📬**\n\n"
                        + progress_str(
                            total=bot_users_count,
                            current=count + len(blocked_users),
                        )
                        + f"\n\n**▾∮تم بنجاح! √ ** :  `{count}`\n"
                        + f"**▾∮يوجد خطأ ✘ ** :  `{len(blocked_users)}`"
                    )
                    await br_cast.edit(prog_)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
    end_ = datetime.now()
    b_info = f"<b>▾∮تم ارسال رسالتك الى «</b><i>{count}</i><b>» مستخدم 📣</b>"
    if len(blocked_users) != 0:
        b_info += f"\n<b>▾∮مجموع المستخدمين ↫ «</b><code>{len(blocked_users)}</code><b>» قاموا بحظر البوت ✕ </b>"
    b_info += (
        f"\n<i>▾∮استغرقت عملية الاذاعة ↫ </i> <code>{time_formatter((end_ - start_).seconds)}</code>"
    )
    await br_cast.edit(b_info, parse_mode="html")

@november.nov_cmd(
    pattern=f"/users$",
    command=("users", plugin_category),                  #بعدين
    info={
        "header": "To get users list who started bot.",
        "description": "To get compelete list of users who started your bot",
        "usage": "{tr}bot_users",
    },
)
async def ban_starters(event):
    "To get list of users who started bot."
    ulist = get_all_starters()
    if len(ulist) == 0:
        return await edit_delete(event, "**▾∮ليس لديك مستخدمين في بوتك!⚠️ **")
    msg = "**▾∮اليكَ قائمة مستخدمين بوتك 🔖↶**\n\n**"
    for user in ulist:
        msg += f"**▾∮ الاسم ⪼ ** `{user.first_name}`\n**▾∮ الايدي ⪼** `{user.user_id}`\n**▾∮ المعرف ⪼** @{user.username}\n**▾∮ تاريخ الاستخدام ⪼** __{user.date}__ \n**▾∮ الرابط ⪼** 「{_format.mentionuser(user.first_name , user.user_id)}」\n\n**⍣ⵧⵧⵧⵧⵧɴᴏᴠᴇᴍʙᴇʀⵧⵧⵧⵧⵧ⍣**\n[▾∮ՏøuƦcε πøνεʍβεƦ 🌦](https://t.me/nneee)\n\n"
    await edit_or_reply(event, msg)


@november.nov_cmd(
    pattern=f"^/ban\s+([\s\S]*)",
    from_users=Config.OWNER_ID,
)
async def ban_botpms(event):
    user_id, reason = await get_user_and_reason(event)
    reply_to = await reply_id(event)
    if not user_id:
        return await event.client.send_message(
            event.chat_id, "**▾∮لم استطع ايجاد المستخدم لحظره ✘**", reply_to=reply_to
        )
    if not reason:
        return await event.client.send_message(
            event.chat_id, "**▾∮اكتب سبب حظره بعد الامر مثل↶**\n`/ban @nneee مزعج،ممل ..الخ`", reply_to=reply_to
        )
    try:
        user = await event.client.get_entity(user_id)
        user_id = user.id
    except Exception as e:
        return await event.reply(f"**▾∮هنالك خطأ ... تحقق ↻**\n`{str(e)}`")
    if user_id == Config.OWNER_ID:
        return await event.reply("**▾∮ كيف لي ان احظر المالك!♕**")
    check = check_is_black_list(user.id)
    if check:
        return await event.client.send_message(
            event.chat_id,
            f"**▾∮ المستخدم من ضمن المحظورين!**\n**▾∮ سبب حظرة من البوت ↫** `{check.reason}`\n**▾∮ تاريخ الحظر ↫** `{check.date}`\n",
        )
    msg = await ban_user_from_bot(user, reason, reply_to)
    await event.reply(msg)


@november.nov_cmd(
    pattern=f"^/unban(?:\s|$)([\s\S]*)",
    from_users=Config.OWNER_ID,
)
async def ban_botpms(event):
    user_id, reason = await get_user_and_reason(event)
    reply_to = await reply_id(event)
    if not user_id:
        return await event.client.send_message(
            event.chat_id, "**▾∮ لا استطيع ايجاد المستخدم لالغاء حظره!**", reply_to=reply_to
        )
    try:
        user = await event.client.get_entity(user_id)
        user_id = user.id
    except Exception as e:
        return await event.reply(f"**▾∮هنالك خطأ ... تحقق ↻**\n`{str(e)}`")
    check = check_is_black_list(user.id)
    if not check:
        return await event.client.send_message(
            event.chat_id,
            f"**▾∮ تم الغاء الحظر مسبقًا للمستخدم ❕↶**\n\n** ▾∮ المستخدم ⪼** 「{_format.mentionuser(user.first_name , user.id)}」\n",
        )
    msg = await unban_user_from_bot(user, reason, reply_to)
    await event.reply(msg)


@november.nov_cmd(
    pattern=f"/banlist/banlist$",
    command=("bblist", plugin_category),
    info={
        "header": "To get users list who are banned in bot.",                           #بعدين
        "description": "To get list of users who are banned in bot.",
        "usage": "{tr}bblist",
    },
)
async def ban_starters(event):
    "**للحصول على قائمة بالمستخدمين المحظورين من البوت**"
    ulist = get_all_bl_users()
    if len(ulist) == 0:
        return await edit_delete(event, "**▾∮ لا يوجد مستخدمين محظورين من البوت ✓**")
    msg = "**▾∮ اليكَ قائمة المحظورين من ببوتك 📮↶**\n\n**"
    for user in ulist:
        msg += f"**▾∮ الاسم ⪼ **`{user.first_name}`\n**▾∮ الايدي ⪼ **`{user.chat_id}`\n**▾∮ المعرف ⪼** @{user.username}\n**▾∮ الرابط ⪼ ** ┕{_format.mentionuser(user.first_name , user.chat_id)}┙\n**▾∮ تاريخ الحظر ⪼** `{user.date}`\n**▾∮ سبب الحظر ⪼** __{user.reason}__\n\n**⍣ⵧⵧⵧⵧⵧɴᴏᴠᴇᴍʙᴇʀⵧⵧⵧⵧⵧ⍣**\n[▾∮ՏøuƦcε πøνεʍβεƦ 🌦](https://t.me/nneee)\n\n"
    await edit_or_reply(event, msg)

@november.nov_cmd(
    pattern=f"/antif  (on|off)$",
    command=("bot_antif", plugin_category),
    info={
        "header": "To enable or disable bot antiflood.",
        "description": "if it was turned on then after 10 messages or 10 edits of same messages in less time then your bot auto loacks them.",
        "usage": [
            "{tr}bot_antif on",
            "{tr}bot_antif off",
        ],
    },
)
async def ban_antiflood(event):
    "To enable or disable bot antiflood."
    input_str = event.pattern_match.group(1)
    if input_str == "on":
        if gvarstatus("bot_antif") is not None:
            return await edit_delete(event, "**▾∮ بالفعل تم تفعيل تحذير التكرار  ✅**")
        addgvar("bot_antif", True)
        await edit_delete(event, "`**▾∮ تم تفعيل تحذير التكرار  ☑️**")
    elif input_str == "off":
        if gvarstatus("bot_antif") is None:
            return await edit_delete(event, "**▾∮ بالفعل تم تعطيل تحذير التكرار ❌**")
        delgvar("bot_antif")
        await edit_delete(event, "**▾∮ بالفعل تم تعطيل تحذير التكرار ✘**")
