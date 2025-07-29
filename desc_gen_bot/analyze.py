from telegram import Update
from telegram.ext import ContextTypes
from clients import mistral
from localdb import append_line_to_file, read_file
from rate_limits import build_filename_for_current_date, create_or_append_request_info, get_current_rate_limit

USER_POSTS_FILENAME = "user_posts/data.txt"
USER_DATA = "user_data"
MAX_REQUESTS_PER_USER_IN_DAY = 10
TASK = "Проверь текст"

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    
    if update.message.chat.type == 'private':
        user_post = ' '.join(context.args)
        user_id = update.effective_user.id
        user_context = read_file(f'{USER_DATA}/{user_id}')

        if user_post == "":
             await update.message.reply_text("Не могу проанализировать пустой текст, попробуйте что-нибудь написать.")
             return
        if len(user_post) > 1000:
            await update.message.reply_text("Текст слишком длинный")
            return
        
        print(user_post)

        # сохраняем запрос в файл для будущего
        append_line_to_file(USER_POSTS_FILENAME, f"-----\n{user_id}\n{user_post}\n-----\n\n")

        current_request_count = get_current_rate_limit(user_id)
        if current_request_count > MAX_REQUESTS_PER_USER_IN_DAY:
            await update.message.reply_text("Вы превысыли вашу дневную квоту на кол-во запросов. Попробуйте завтра или оформите подписку.")
            return
        
        print(f"{user_id}: {current_request_count} + 1 request for analyze")
        create_or_append_request_info(build_filename_for_current_date(user_id), current_request_count+1)

        await update.message.reply_text("Обрабатываю запрос... 🤓")
        analyze_result = mistral.req(f"{TASK} {user_post}", user_context)
        await update.message.reply_text(analyze_result)