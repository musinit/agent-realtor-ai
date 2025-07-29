import texts
from telegram import Update
from typing import Optional
from telegram.ext import  ContextTypes
from localdb import create_and_set_append_only, append_line_to_file, file_exists, user_data_path

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    filename = f"{user_data_path}/{user_id}"
    if not file_exists(filename):
        create_and_set_append_only(filename)
        append_line_to_file(filename, "")

    await update.message.reply_text(texts.WELCOME_TEXT)
