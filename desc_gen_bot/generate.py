from telegram import Update
from telegram.ext import ContextTypes
from clients import mistral
from localdb import append_line_to_file, read_file
from rate_limits import build_filename_for_current_date, create_or_append_request_info, get_current_rate_limit

USER_POSTS_FILENAME = "user_posts/data.txt"
USER_DATA = "user_data"
MAX_REQUESTS_PER_USER_IN_DAY = 10
TASK = "таска"

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    
    if update.message.chat.type == 'private':
        user_id = update.effective_user.id
        user_context = read_file(f'{USER_DATA}/{user_id}')

        current_request_count = get_current_rate_limit(user_id)
        if current_request_count > MAX_REQUESTS_PER_USER_IN_DAY:
            await update.message.reply_text("Вы превысыли вашу дневную квоту на кол-во запросов. Попробуйте завтра или оформите подписку.")
            return
        
        print(f"{user_id}: {current_request_count} + 1 request for generate")
        create_or_append_request_info(build_filename_for_current_date(user_id), current_request_count+1)

        await update.message.reply_text("Обрабатываю запрос... 🤓")
        result = mistral.req(TASK, user_context)
        await update.message.reply_text(result)