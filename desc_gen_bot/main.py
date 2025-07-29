import logging
import const
import texts
from telegram import Update
from typing import Optional
from telegram.ext import Updater, ApplicationBuilder, CommandHandler, MessageHandler, ChatMemberHandler, filters, ContextTypes
import start
from process_input import process_input
from track_chats import show_chats, track_chats
from error import error
from analyze import analyze
from generate import generate
from help import help_command
from user_steps import UserSteps




# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def main() -> None:
    # Create the Application and pass it your bot's token
    application = ApplicationBuilder().token(const.DESC_GEN_BOT_TOKEN).build()

    # Add command and message handlers
    application.add_handler(CommandHandler("start", start.start))
    application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_input))
    application.add_handler(MessageHandler(filters.PHOTO, process_input))
    application.add_handler(CommandHandler("analyze", analyze))
    application.add_handler(CommandHandler("generate", generate))
    application.add_handler(CommandHandler("help", help_command))
    application.add_error_handler(error)


    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)



if __name__ == '__main__':
    main()