from telegram import Update
from telegram.ext import CallbackContext
import texts

async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(texts.HELP_TEXT)