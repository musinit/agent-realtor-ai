import logging
from localdb import append_line_to_file
from typing import Optional
from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.ext import CallbackContext, ContextTypes

# Enable logging
LOG_FOLDER = "logs"
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def show_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows which chats the bot is in"""
    user_ids = ", ".join(str(uid) for uid in context.bot_data.setdefault("user_ids", set()))
    group_ids = ", ".join(str(gid) for gid in context.bot_data.setdefault("group_ids", set()))
    channel_ids = ", ".join(str(cid) for cid in context.bot_data.setdefault("channel_ids", set()))
    text = (
        f"@{context.bot.username} is currently in a conversation with the user IDs {user_ids}."
        f" Moreover it is a member of the groups with IDs {group_ids} "
        f"and administrator in the channels with IDs {channel_ids}."
    )
    await update.effective_message.reply_text(text)


def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tracks the chats the bot is in."""
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    was_member, is_member = result

    # Let's check who is responsible for the change
    cause_name = update.effective_user.full_name

    # Handle chat types differently:
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        if not was_member and is_member:
            # This may not be really needed in practice because most clients will automatically
            # send a /start command after the user unblocks the bot, and start_private_chat()
            # will add the user to "user_ids".
            # We're including this here for the sake of the example.
            logger.info("{} разблокировал бота", cause_name)
            context.bot_data.setdefault("user_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("{} заблокировал", cause_name)
            context.bot_data.setdefault("user_ids", set()).discard(chat.id)
    elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if not was_member and is_member:
            msg = "{} добавил бота в группу {}".format(cause_name, chat.title)
            logger.info(msg)
            context.bot_data.setdefault("group_ids", set()).add(chat.id)
            append_line_to_file(f"{LOG_FOLDER}/log.txt", msg)
        elif was_member and not is_member:
            msg = "{} удалил бота из группы {}".format(cause_name, chat.title)
            logger.info(msg)
            context.bot_data.setdefault("group_ids", set()).discard(chat.id)
            append_line_to_file(f"{LOG_FOLDER}/log.txt", msg)
    elif not was_member and is_member:
        msg = "{} добавил бота в канал {}".format(cause_name, chat.title)
        logger.info(msg)
        context.bot_data.setdefault("channel_ids", set()).add(chat.id)
        append_line_to_file(f"{LOG_FOLDER}/log.txt", msg)
    elif was_member and not is_member:
        msg = "{} удалил бота из канала {}".format(cause_name, chat.title)
        logger.info(msg)
        context.bot_data.setdefault("channel_ids", set()).discard(chat.id)
        append_line_to_file(f"{LOG_FOLDER}/log.txt", msg)
