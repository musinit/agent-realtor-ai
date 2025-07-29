import os
import sys
import logging

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
import tempfile
import asyncio
from telegram import InputMediaPhoto
from dotenv import load_dotenv

# --- Add project root to sys.path ---
# This is to ensure that the bot can import the client modules
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from two_gis_client import TwoGisClient
from openai_client import OpenAIClient

# Load environment variables from .env file
# load_dotenv() # Temporarily remove dotenv

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- State definitions for conversation ---
PHOTOS, ADDRESS, USER_PROMPT, FEEDBACK = range(4)


# --- Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message and a button to start the process."""
    reply_keyboard = [["Начать создание описания"]]
    await update.message.reply_text(
        "Привет! Я ваш AI помощник в создании продающего описания для недвижимости. "
        "Нажмите кнопку ниже, чтобы начать.",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return ConversationHandler.END # End any previous conversation

async def start_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the description creation process."""
    context.user_data['photos'] = [] # Initialize photos list
    context.user_data['photo_paths'] = [] # Initialize photo paths list
    
    button_text = "Шаг завершен, перейти к следующему"
    
    await update.message.reply_text(
        "Отлично! Давайте начнем. Пожалуйста, отправьте мне фотографии вашей "
        "недвижимости. Можно отправлять как фотографии, так и фото в непожатом виде (предпочтительно). Когда все нужные фото будут загружены, нажмите кнопку 'Шаг завершен, перейти к следующему'.",
        reply_markup=ReplyKeyboardMarkup([[button_text]], resize_keyboard=True),
    )
    return PHOTOS

async def save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores photos sent as either compressed photo or uncompressed document."""
    user = update.message.from_user
    photo_file = None
    
    if update.message.photo:
        # User sent a compressed photo
        photo_file = await update.message.photo[-1].get_file()
        logger.info("Photo (as photo) received from %s", user.first_name)
    elif update.message.document and update.message.document.mime_type.startswith('image/'):
        # User sent an uncompressed image file
        photo_file = await update.message.document.get_file()
        logger.info("Photo (as document) received from %s", user.first_name)
    
    if photo_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_photo:
            await photo_file.download_to_drive(temp_photo.name)
            context.user_data['photos'].append(photo_file.file_id) # keep file_id for sending back
            context.user_data['photo_paths'].append(temp_photo.name) # save path for openai
    
    return PHOTOS # Stay in the same state to receive more photos


async def photos_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Moves to the next step after user is done sending photos."""
    user = update.message.from_user
    photos_list = context.user_data.get('photos', [])
    logger.info("User %s finished uploading %d photos.", user.first_name, len(photos_list))
    
    if not photos_list:
        await update.message.reply_text(
            "Вы не добавили ни одной фотографии. Пожалуйста, отправьте хотя бы одну."
        )
        return PHOTOS

    await update.message.reply_text(
        'Отлично! Теперь, пожалуйста, введите точный адрес объекта одним сообщением.',
        reply_markup=ReplyKeyboardRemove(),
    )
    return ADDRESS


async def address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the address and asks for a user prompt."""
    user_address = update.message.text
    context.user_data['address'] = user_address
    await update.message.reply_text(
        'Адрес сохранен. Теперь введите дополнительную информацию, которую считаете важной '
        '(например, количество комнат, площадь, особенности ремонта, какие '
        'дополнительные продажные особенности объекта).'
    )
    return USER_PROMPT


async def user_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Stores the user prompt, triggers the description generation, 
    and ends the conversation.
    """
    user_prompt_text = update.message.text
    context.user_data['user_prompt'] = user_prompt_text
    chat_id = update.effective_chat.id

    await context.bot.send_message(
        chat_id=chat_id,
        text="Спасибо! Я собрал всю информацию. Начинаю генерацию описания. Это может занять некоторое время..."
    )

    # Trigger the async description generation
    asyncio.create_task(generate_and_send_description(update, context))

    return ConversationHandler.END


async def generate_and_send_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    An async helper function to generate and send the description, 
    allowing the bot to remain responsive.
    """
    chat_id = update.effective_chat.id
    try:
        # --- 1. Get data from context ---
        photo_paths = context.user_data.get('photo_paths', [])
        address = context.user_data.get('address')
        user_prompt_text = context.user_data.get('user_prompt')

        # --- 2. Initialize clients ---
        openai_client = context.bot_data['openai_client']
        two_gis_client = context.bot_data['two_gis_client']

        # --- 3. Fetch infrastructure and generate description ---
        infra_summary = two_gis_client.get_infrastructure_summary(address)
        description = openai_client.create_description(
            user_prompt=user_prompt_text,
            infrastructure_summary=infra_summary,
            image_paths=photo_paths,
            address=address,
        )

        # --- 4. Send Result ---
        # Send photos first as a media group
        photo_ids = context.user_data.get('photos', [])
        if photo_ids:
            media_group = [InputMediaPhoto(media=pid) for pid in photo_ids]
            # We can only send up to 10 photos in a media group
            await context.bot.send_media_group(chat_id=chat_id, media=media_group[:10])

        await context.bot.send_message(
            chat_id=chat_id,
            text="🎉 Ваше описание готово! 🎉"
        )

        # A simple replacement to fix bolding issues from the model
        final_description = description.replace('**', '*')

        await context.bot.send_message(
            chat_id=chat_id,
            text=final_description,
            parse_mode='Markdown' # Fall back to simple Markdown, it's more forgiving
        )
        # We will ask for feedback in the next step
            
    except Exception as e:
        logger.error("Error during description generation for chat %d: %s", chat_id, e, exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Произошла ошибка при создании описания: {e}\nПопробуйте начать заново с команды /start"
        )
    finally:
        # Clean up user data and temporary files
        for path in context.user_data.get('photo_paths', []):
            try:
                os.remove(path)
            except OSError:
                pass
        context.user_data.clear()


async def post_init(application: Application):
    """
    Post-initialization function to set bot commands.
    """
    await application.bot.set_my_commands([
        BotCommand("start", "Запустить/перезапустить бота"),
    ])

def main() -> None:
    """Run the bot."""
    # --- Initialize clients ---
    load_dotenv()
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    two_gis_api_key = os.environ.get("TWOGIS_API_KEY")
    telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if not all([openai_api_key, two_gis_api_key, telegram_bot_token]):
        logger.error("One or more environment variables are missing.")
        return

    openai_client = OpenAIClient(api_key=openai_api_key)
    two_gis_client = TwoGisClient(api_key=two_gis_api_key)

    # --- Bot Setup ---
    application = Application.builder().token(telegram_bot_token).post_init(post_init).build()
    
    # Store clients in bot_data
    application.bot_data['openai_client'] = openai_client
    application.bot_data['two_gis_client'] = two_gis_client

    # --- Conversation Handler ---
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Начать создание описания$'), start_description)],
        states={
            PHOTOS: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, save_photo),
                MessageHandler(filters.Regex('^Шаг завершен, перейти к следующему$'), photos_done)
            ],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, address)],
            USER_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_prompt)],
            FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback)]
        },
        fallbacks=[],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    # --- Start Bot ---
    logger.info("Bot is starting...")
    application.run_polling()


if __name__ == '__main__':
    main() 