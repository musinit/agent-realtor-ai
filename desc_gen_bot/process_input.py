from telegram import Update
from telegram.ext import ContextTypes
from user_steps import UserSteps
import base64
from clients import two_gis_client, openai_client
import os
import time

step_to_reply_msg = {
    0: "Спасибо за адрес. Далее загрузите фотографию квартиры.",
    1: "Спасибо за фотографии. Для составления описания мне нужно еще несколько деталей. Напишите одним сообщением в свободной форме основные данные о квартире, которые вы хотите отразить в описании (например, этаж, планировка, ремонт, вид из окна).",
    2: "Спасибо за данные о квартире. Предпоследний шаг - напишите одним сообщением в свободной форме основные данные о доме (например, год постройки, тип дома, наличие удобств в виде консьержа и т.п.).",
    3: "Спасибо за данные о доме. Описание почти готово. Последним шагом напишите условия сделки (например, про тип сделки, юр чистота, сколько собственников).",
    4: "Спасибо за доп.детали, генерируем финальное описание ..."
}

user_steps = UserSteps()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TWOGIS_API_KEY = os.environ.get("TWOGIS_API_KEY")

async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if update.message.chat.type == 'private':
        channel_info = ""
        user_message = ""
        if context.args is not None:
            channel_info = ' '.join(context.args)
            if channel_info == "":
                await update.message.reply_text("Пустой текст не подходит, пришлите что-то:)")
                return
        else:
            user_message = update.message.text

        user_id = update.effective_user.id

        current_user_step = user_steps.get_current_user_step(user_id)


        if current_user_step <= 4:
            reply_msg = step_to_reply_msg[current_user_step]
            if current_user_step == 0:
                await update.message.reply_text("Ищу супермаркеты, торговые центры, станции метро и другие обьекты поблизости...")
                client = two_gis_client.TwoGisClient(api_key=TWOGIS_API_KEY)
                infra_summary = client.get_infrastructure_summary(user_message)
                user_steps.update_user_data(user_id, address = user_message)
                user_steps.update_user_data(user_id, infra_summary = infra_summary)
            if current_user_step == 1:
                if len(update.message.photo) < 1:
                    print("not a photo")
                    return
                photo_file = await update.message.photo[-1].get_file()
                image_bytes = await photo_file.download_as_bytearray()
                base64_image = base64.b64encode(image_bytes).decode("utf-8")
                user_steps.update_user_data(user_id, image = base64_image)
            if current_user_step == 2:
                user_steps.update_user_data(user_id, flat_description = user_message)
            if current_user_step == 3:
                user_steps.update_user_data(user_id, options = user_message)
            if current_user_step == 4:
                user_steps.update_user_data(user_id, deal_details = user_message)

        if current_user_step == 4:
            reply_msg = "Спасибо, генерирую финальное описание ... 🤓"
            await update.message.reply_text(reply_msg)

            current_user_steps = user_steps.get_current_user_data(user_id)
            ai_client = openai_client.OpenAIClient(api_key=OPENAI_API_KEY)
            user_promt = f"Адрес: {current_user_steps._address}\nОписание квартиры: {current_user_steps._flat_description}\nОписание дома: {current_user_steps._options}\nУсловия сделки: {current_user_steps._deal_details}"

            description = ai_client.create_description(
                user_prompt=user_promt,
                address=current_user_steps._address,
                infrastructure_summary=current_user_steps._infra_summary,
                image_paths=current_user_steps._image
            )
            #resp = mistral.req_final_description(user_id, current_user_steps)

            reply_msg = description


        current_user_data = user_steps.get_current_user_data(user_id)
        await update.message.reply_text(reply_msg)

        if current_user_step == 4:
            time.sleep(3)
            await update.message.reply_text("Чтобы попробовать снова - просто введите адрес обьекта недвижимости.")

        user_steps.increment_user_step(user_id)

   
        
