import html
import time
from datetime import datetime
from io import BytesIO

from telegram import ParseMode, Update
from telegram.error import BadRequest, TelegramError, Unauthorized
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)
from telegram.utils.helpers import mention_html

import DevXRobot.modules.sql.global_bans_sql as sql
from DevXRobot.modules.sql.users_sql import get_user_com_chats
from DevXRobot import (
    DEV_USERS,
    EVENT_LOGS,
    OWNER_ID,
    STRICT_GBAN,
    DRAGONS,
    SUPPORT_CHAT,
    SPAMWATCH_SUPPORT_CHAT,
    DEMONS,
    TIGERS,
    WOLVES,
    sw,
    dispatcher,
)
from DevXRobot.modules.helper_funcs.chat_status import (
    is_user_admin,
    support_plus,
    user_admin,
)
from DevXRobot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from DevXRobot.modules.helper_funcs.misc import send_to_list

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
    "Can't remove chat owner",
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
    "Peer_id_invalid",
    "User not found",
}


@run_async
@support_plus
def gban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    if int(user_id) in DEV_USERS:
        message.reply_text(
            "That user is part of the Association\nI can't act against our own."
        )
        return

    if int(user_id) in DRAGONS:
        message.reply_text(
            "I spy, with my little eye... a disaster! Why are you guys turning on each other?"
        )
        return

    if int(user_id) in DEMONS:
        message.reply_text(
            "OOOH someone's trying to gban a Demon Disaster! *grabs popcorn*"
        )
        return

    if int(user_id) in TIGERS:
        message.reply_text("That's a Tiger! They cannot be banned!")
        return

    if int(user_id) in WOLVES:
        message.reply_text("That's a Wolf! They cannot be banned!")
        return

    if user_id == bot.id:
        message.reply_text("You uhh...want me to punch myself?")
        return

    if user_id in [777000, 1087968824]:
        message.reply_text("Fool! You can't attack Telegram's native tech!")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user.")
            return ""
        else:
            return

    if user_chat.type != "private":
        message.reply_text("That's not a user!")
        return

    if sql.is_user_gbanned(user_id):

        if not reason:
            message.reply_text(
                "This user is already gbanned; I'd change the reason, but you haven't given me one..."
            )
            return

        old_reason = sql.update_gban_reason(
            user_id, user_chat.username or user_chat.first_name, reason
        )
        if old_reason:
            message.reply_text(
                "This user is already gbanned😹, for the following reason:\n"
                "<code>{}</code>\n"
                "I've gone and updated it with your new reason!".format(
                    html.escape(old_reason)
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            message.reply_text(
                "This user is already gbanned😹, but had no reason set; I've gone and updated it!"
            )

        return

    message.reply_text("𝚆𝙰𝙸𝚃 𝙳𝚄𝙳𝙴 𝙸'𝙼 𝙶𝙱𝙰𝙽𝙽𝙸𝙽𝙶 𝚃𝙷𝙸𝚂 𝙽𝙸𝙶𝙶𝙰😼💣")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != "private":
        chat_origin = "<b>{} ({})</b>\n".format(html.escape(chat.title), chat.id)
    else:
        chat_origin = "<b>{}</b>\n".format(chat.id)

    log_message = (
        f"#𝙶𝙱𝙰𝙽𝙽𝙴𝙳_𝙾𝙿\n"
        f"<b>𝙶𝙱𝙰𝙽𝙽𝙴𝙳 𝙵𝚁𝙾𝙼:</b> <code>{chat_origin}</code>\n"
        f"<b>𝚁𝙴𝚂𝙿𝙾𝙽𝚂𝙸𝙱𝙻𝙴 𝙰𝙳𝙼𝙸𝙽:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>𝙱𝙰𝙽𝙽𝙴𝙳 𝙽𝙸𝙶𝙶𝙰:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>𝙽𝙸𝙶𝙶𝙰'𝚂 𝙸𝙳:</b> <code>{user_chat.id}</code>\n"
        f"<b>𝙴𝚅𝙴𝙽𝚃 𝚂𝚃𝙰𝙼𝙿:</b> <code>{current_time}</code>"
    )

    if reason:
        if chat.type == chat.SUPERGROUP and chat.username:
            log_message += f'\n<b>Reason:</b> <a href="https://telegram.me/{chat.username}/{message.message_id}">{reason}</a>'
        else:
            log_message += f"\n<b>Reason:</b> <code>{reason}</code>"

    if EVENT_LOGS:
        try:
            log = bot.send_message(EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                EVENT_LOGS,
                log_message
                + "\n\nFormatting has been disabled due to an unexpected error.",
            )

    else:
        send_to_list(bot, DRAGONS + DEMONS, log_message, html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_user_com_chats(user_id)
    gbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
            gbanned_chats += 1

        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text(f"Could not gban due to: {excp.message}")
                if EVENT_LOGS:
                    bot.send_message(
                        EVENT_LOGS,
                        f"Could not gban due to {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    send_to_list(
                        bot, DRAGONS + DEMONS, f"Could not gban due to: {excp.message}"
                    )
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    if EVENT_LOGS:
        log.edit_text(
            log_message + f"\n<b>Chats affected:</b> <code>{gbanned_chats}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        send_to_list(
            bot,
            DRAGONS + DEMONS,
            f"Gban complete! (User banned in <code>{gbanned_chats}</code> chats)",
            html=True,
        )

    end_time = time.time()
    gban_time = round((end_time - start_time), 2)

    if gban_time > 60:
        gban_time = round((gban_time / 60), 2)
        message.reply_text("𝙶𝙱𝙰𝙽 𝙳𝙾𝙽𝙴⚔️!! 𝙽𝙾𝚆 𝚃𝙷𝙸𝚂 𝙽𝙸𝙶𝙶𝙰 𝙵𝚄𝙲𝙺𝙴𝙳 𝚄𝙿 𝙷𝙰𝚁𝙳 𝙻𝙾𝙻 𝙺𝙸𝙳𝙳😼.", parse_mode=ParseMode.HTML)
    else:
        message.reply_text("𝙶𝙱𝙰𝙽 𝙳𝙾𝙽𝙴⚔️!! 𝙽𝙾𝚆 𝚃𝙷𝙸𝚂 𝙽𝙸𝙶𝙶𝙰 𝙵𝚄𝙲𝙺𝙴𝙳 𝚄𝙿 𝙷𝙰𝚁𝙳 𝙻𝙾𝙻 𝙺𝙸𝙳𝙳😼.", parse_mode=ParseMode.HTML)

    try:
        bot.send_message(
            user_id,
            "#EVENT"
            "You have been marked as Malicious and as such have been banned from any future groups we manage."
            f"\n<b>𝚁𝙴𝙰𝚂𝙾𝙽 𝙵𝙾𝚁 𝙱𝙰𝙽𝙽:</b> <code>{html.escape(user.reason)}</code>"
            f"</b>𝙰𝙿𝙿𝙴𝙰𝙻 𝙲𝙷𝙰𝚃:</b> @{SUPPORT_CHAT}",
            parse_mode=ParseMode.HTML,
        )
    except:
        pass  # bot probably blocked by user


@run_async
@support_plus
def ungban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "𝚈𝚘𝚞 𝚍𝚘𝚗'𝚝 𝚜𝚎𝚎𝚖 𝚝𝚘 𝚋𝚎 𝚛𝚎𝚏𝚎𝚛𝚛𝚒𝚗𝚐 𝚝𝚘 𝚊 𝚞𝚜𝚎𝚛 𝚘𝚛 𝚝𝚑𝚎 𝙸𝙳 𝚜𝚙𝚎𝚌𝚒𝚏𝚒𝚎𝚍 𝚒𝚜 𝚒𝚗𝚌𝚘𝚛𝚛𝚎𝚌𝚝..𝙻𝚘𝚕 𝚃𝚑𝚒𝚜 𝚔𝚒𝚍𝚍 𝚒𝚜 𝚒𝚗𝚗𝚘𝚌𝚎𝚗𝚝🤭🤔"
        )
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != "private":
        message.reply_text("That's not a user👊👊!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("This user is not gbanned♻️!")
        return

    message.reply_text(f"𝙾𝙺 𝙸 𝚆𝙸𝙻𝙻 𝙶𝙸𝙱 {user_chat.first_name} 𝙰 𝚂𝙴𝙲𝙾𝙽𝙳 𝙲𝙷𝙰𝙽𝙲𝙴 𝙶𝙻𝙾𝙱𝙰𝙻𝙻𝚈 , 𝙶𝙾 𝙽𝙳 𝙿𝙻𝙰𝚈 𝙵𝚁𝙴𝙴𝙻𝚈 𝙺𝙸𝙳𝙳😁.")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != "private":
        chat_origin = f"<b>{html.escape(chat.title)} ({chat.id})</b>\n"
    else:
        chat_origin = f"<b>{chat.id}</b>\n"

    log_message = (
        f"#𝚄𝙽𝙶𝙱𝙰𝙽𝙽𝙴𝙳_𝙾𝙿🔱\n"
        f"<b>𝚄𝙽𝙱𝙰𝙽𝙽𝙴𝙳 𝙵𝚁𝙾𝙼:</b> <code>{chat_origin}</code>\n"
        f"<b>𝙰𝙳𝙼𝙸𝙽:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>𝚄𝙽𝙱𝙰𝙽𝙽𝙴𝙳 𝙺𝙸𝙳𝙳𝙾:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>𝙺𝙸𝙳𝙳𝙾'𝚂 𝙸𝙳:</b> <code>{user_chat.id}</code>\n"
        f"<b>𝙴𝚅𝙴𝙽𝚃 𝚂𝚃𝙰𝙼𝙿:</b> <code>{current_time}</code>"
    )

    if EVENT_LOGS:
        try:
            log = bot.send_message(EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                EVENT_LOGS,
                log_message
                + "\n\nFormatting has been disabled due to an unexpected error.",
            )
    else:
        send_to_list(bot, DRAGONS + DEMONS, log_message, html=True)

    chats = get_user_com_chats(user_id)
    ungbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == "kicked":
                bot.unban_chat_member(chat_id, user_id)
                ungbanned_chats += 1

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text(f"Could not un-gban due to: {excp.message}")
                if EVENT_LOGS:
                    bot.send_message(
                        EVENT_LOGS,
                        f"Could not un-gban due to: {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    bot.send_message(
                        OWNER_ID, f"Could not un-gban due to: {excp.message}"
                    )
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    if EVENT_LOGS:
        log.edit_text(
            log_message + f"\n<b>Chats affected:</b> {ungbanned_chats}",
            parse_mode=ParseMode.HTML,
        )
    else:
        send_to_list(bot, DRAGONS + DEMONS, "un-gban complete!")

    end_time = time.time()
    ungban_time = round((end_time - start_time), 2)

    if ungban_time > 60:
        ungban_time = round((ungban_time / 60), 2)
        message.reply_text(f"𝙻𝙾𝙻 𝙾𝙺 𝙼𝙰𝚂𝚃𝙴𝚁 𝙸 𝙰𝙼 𝙶𝙾𝙸𝙽𝙶 𝚃𝙾 𝚄𝙽𝙶𝙱𝙰𝙽 𝚃𝙷𝙸𝚂 𝙽𝙾𝙾𝙱 𝙶𝚁𝙾𝚆 𝚄𝙿 𝙺𝙸𝙳𝙳 𝚃𝙷𝙴𝙽 𝙲𝙾𝙼𝙴 𝙵𝙾𝚁 𝙵𝙸𝙶𝙷𝚃😼😹, 𝚄𝙽𝙱𝙰𝙽𝙽𝙴𝙳 𝙸𝙽 {ungban_time} 𝚖𝚒𝚗")
    else:
        message.reply_text(f"𝙻𝙾𝙻 𝙾𝙺 𝙼𝙰𝚂𝚃𝙴𝚁 𝙸 𝙰𝙼 𝙶𝙾𝙸𝙽𝙶 𝚃𝙾 𝚄𝙽𝙶𝙱𝙰𝙽 𝚃𝙷𝙸𝚂 𝙽𝙾𝙾𝙱 𝙶𝚁𝙾𝚆 𝚄𝙿 𝙺𝙸𝙳𝙳 𝚃𝙷𝙴𝙽 𝙲𝙾𝙼𝙴 𝙵𝙾𝚁 𝙵𝙸𝙶𝙷𝚃😼😹, 𝚄𝙽𝙱𝙰𝙽𝙽𝙴𝙳 𝙸𝙽 {ungban_time} 𝚜𝚎𝚌")


@run_async
@support_plus
def gbanlist(update: Update, context: CallbackContext):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text(
            "There aren't any gbanned users! You're kinder than I expected..."
        )
        return

    banfile = "Screw these guys.\n"
    for user in banned_users:
        banfile += f"[x] {user['name']} - {user['user_id']}\n"
        if user["reason"]:
            banfile += f"Reason: {user['reason']}\n"

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="Here is the list of currently gbanned users.",
        )


def check_and_ban(update, user_id, should_message=True):

    chat = update.effective_chat  # type: Optional[Chat]
    try:
        sw_ban = sw.get_ban(int(user_id))
    except:
        sw_ban = None

    if sw_ban:
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text(
                f"<b>𝙰𝙻𝙴𝙰𝚁𝚃 𝙶𝚄𝚈𝚂⚠️</b>: 𝚃𝙷𝙸𝚂 𝚂𝚃𝚄𝙿𝙸𝙳 𝙺𝙸𝙳𝙳 𝙸𝚉 𝙶𝙻𝙾𝙱𝙴𝙻𝙻𝚈 𝙱𝙰𝙽𝙽𝙴𝙳.\n"
                f"<code>*𝙱𝙰𝙽 𝙷𝙸𝙼 𝙵𝚁𝙾𝙼 𝙷𝙴𝚁𝙴*</code>.\n"
                f"<b>𝙰𝙿𝙿𝙴𝙰𝙻 𝙲𝙷𝙰𝚃</b>: {SPAMWATCH_SUPPORT_CHAT}\n"
                f"<b>𝙺𝙸𝙳𝙳𝙾'𝚂 𝙸𝙳</b>: <code>{sw_ban.id}</code>\n"
                f"<b>𝙱𝙰𝙽𝙽𝙴𝙳 𝚁𝙴𝙰𝚂𝙾𝙽</b>: <code>{html.escape(sw_ban.reason)}</code>",
                parse_mode=ParseMode.HTML,
            )
        return

    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            text = (
                f"<b>𝙰𝙻𝙴𝙰𝚁𝚃 𝙶𝚄𝚈𝚂⚠️</b>: 𝚃𝙷𝙸𝚂 𝚂𝚃𝚄𝙿𝙸𝙳 𝙺𝙸𝙳𝙳 𝙸𝚉 𝙶𝙻𝙾𝙱𝙴𝙻𝙻𝚈 𝙱𝙰𝙽𝙽𝙴𝙳.\n"
                f"<code>*𝙱𝙰𝙽 𝙷𝙸𝙼 𝙵𝚁𝙾𝙼 𝙷𝙴𝚁𝙴*</code>.\n"
                f"<b>𝙰𝙿𝙿𝙴𝙰𝙻 𝙲𝙷𝙰𝚃</b>: @{SUPPORT_CHAT}\n"
                f"<b>𝙺𝙸𝙳𝙳𝙾'𝚂 𝙸𝙳</b>: <code>{user_id}</code>"
            )
            user = sql.get_gbanned_user(user_id)
            if user.reason:
                text += f"\n<b>𝙱𝙰𝙽𝙽𝙴𝙳 𝚁𝙴𝙰𝚂𝙾𝙽:</b> <code>{html.escape(user.reason)}</code>"
            update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def enforce_gban(update: Update, context: CallbackContext):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    bot = context.bot
    try:
        restrict_permission = update.effective_chat.get_member(
            bot.id
        ).can_restrict_members
    except Unauthorized:
        return
    if sql.does_chat_gban(update.effective_chat.id) and restrict_permission:
        user = update.effective_user
        chat = update.effective_chat
        msg = update.effective_message

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)
            return

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@run_async
@user_admin
def gbanstat(update: Update, context: CallbackContext):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "Antispam is now enabled ✅ "
                "I am now protecting your group from potential remote threats!"
            )
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "Antispan is now disabled ❌ " "Spamwatch is now disabled ❌"
            )
    else:
        update.effective_message.reply_text(
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {}\n"
            "When True, any gbans that happen will also happen in your group. "
            "When False, they won't, leaving you at the possible mercy of "
            "spammers.".format(sql.does_chat_gban(update.effective_chat.id))
        )


def __stats__():
    return f"• {sql.num_gbanned_users()} gbanned users."


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)
    text = "Malicious: <b>{}</b>"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == dispatcher.bot.id:
        return ""
    if int(user_id) in DRAGONS + TIGERS + WOLVES:
        return ""
    if is_gbanned:
        text = text.format("Yes")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += f"\n<b>𝙱𝙰𝙽𝙽𝙴𝙳 𝚁𝙴𝙰𝚂𝙾𝙽:</b> <code>{html.escape(user.reason)}</code>"
        text += f"\n<b>𝙰𝙿𝙿𝙴𝙰𝙻 𝙲𝙷𝙰𝚃:</b> @{SUPPORT_CHAT}"
    else:
        text = text.format("???")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"This chat is enforcing *gbans*: `{sql.does_chat_gban(chat_id)}`."


GBAN_HANDLER = CommandHandler("gban", gban)
UNGBAN_HANDLER = CommandHandler("ungban", ungban)
GBAN_LIST = CommandHandler("gbanlist", gbanlist)

GBAN_STATUS = CommandHandler("antispam", gbanstat, filters=Filters.group)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

__mod_name__ = "Anti-Spam"
__handlers__ = [GBAN_HANDLER, UNGBAN_HANDLER, GBAN_LIST, GBAN_STATUS]

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
    __handlers__.append((GBAN_ENFORCER, GBAN_ENFORCE_GROUP))
