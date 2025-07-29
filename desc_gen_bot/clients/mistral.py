from mistralai import Mistral
from telegram import Update
from telegram.ext import ContextTypes
import os

# можно тестить, но без фанатизма
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
model = "mistral-medium-latest"

context = f"Ты — профессиональный помощник риэлтора. Твоя задача — создавать привлекательные и точные описания квартир для размещения на Авито и Циан. Ни в коем случае не выдумывай факты при составлении описаний, иначе я тебя уволю!" \
"На основе следующих данных: "  \
"1. Адрес: {address} "  \
"2. Описание квартиры (в свободной форме): {flat_description} "  \
"3. Описание дома (в свободной форме): {options} "  \
"А также информации об инфраструктуре рядом (берётся через API), ты должен сгенерировать качественное описание квартиры. "  \


def req(message, system_message):
    if message == "":
        return

    client = Mistral(api_key=MISTRAL_API_KEY)

    chat_response = client.chat.complete(
        model = model,
        messages = [
            {
                "role": "user",
                "content": f"{message}",
            },
            {
                "role": "system",
                "content": f"{system_message}"
            }
        ]
    )

    return chat_response.choices[0].message.content

def req_final_description(user_id, user_steps):
    address = user_steps._address
    flat_description = user_steps._flat_description
    options = user_steps._options

    llm_req = context.format(address=address, flat_description = flat_description, options = options )
    client = Mistral(api_key=MISTRAL_API_KEY)

    chat_response = client.chat.complete(
        model = model,
        messages = [
            {
                "role": "user",
                "content": f"{llm_req}",
            }
            # {
            #     "role": "system",
            #     "content": f"{system_message}"
            # }
        ]
    )

    return chat_response.choices[0].message.content