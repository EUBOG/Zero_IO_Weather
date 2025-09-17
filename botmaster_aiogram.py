import os
import logging
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hbold, hitalic
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализируем бота и диспетчер
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


def get_joke():
    """Шутка — замена icanhazdadjoke.com"""
    try:
        response = requests.get("https://v2.jokeapi.dev/joke/Any?safe-mode")
        data = response.json()
        if data["type"] == "single":
            return data["joke"]
        else:
            return f"{data['setup']}\n{data['delivery']}"
    except Exception as e:
        return f"❌ Ошибка при получении шутки: {e}"


def get_bored_activity():
    """Занятие — замена boredapi.com"""
    try:
        response = requests.get("https://apis.scrimba.com/bored/api/activity")
        data = response.json()

        # Словарь перевода типов активностей
        type_translations = {
            "education": "Образование",
            "recreational": "Развлечения",
            "social": "Социальное",
            "diy": "Сделай сам",
            "charity": "Благотворительность",
            "cooking": "Готовка",
            "relaxation": "Отдых",
            "music": "Музыка",
            "busywork": "Занятость"
        }

        # Переводим тип, если он есть в словаре, иначе оставляем как есть
        translated_type = type_translations.get(data['type'], data['type'].capitalize())

        return (
            f"💡 *{data['activity']}*\n"
            f"Тип: {translated_type}\n"
            f"Участников: {data['participants']}\n"
            f"Цена: {data['price']}/10"
        )
    except Exception as e:
        return f"❌ Ошибка при получении активности: {e}"


def get_number_fact():
    """Факт о числе — замена numbersapi.com"""
    try:
        response = requests.get("https://uselessfacts.jsph.pl/random.json?language=ru")
        data = response.json()
        return data["text"]  # Текст факта на русском
    except Exception as e:
        return f"❌ Ошибка при получении факта: {e}"

def get_cat_image():
    """Котик — замена random.cat"""
    try:
        response = requests.get("https://api.thecatapi.com/v1/images/search")
        data = response.json()
        return data[0]["url"]
    except Exception as e:
        return None  # Вернём None, чтобы обработать ошибку в хендлере


def get_pokemon_info(pokemon_name):
    """Покемон — уже работает"""
    try:
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
        response = requests.get(url)
        if response.status_code != 200:
            return f"❌ Покемон '{pokemon_name}' не найден. Попробуй другое имя."

        data = response.json()
        abilities = ", ".join([a['ability']['name'] for a in data['abilities'][:3]])
        types = ", ".join([t['type']['name'] for t in data['types']])
        image_url = data['sprites']['other']['official-artwork']['front_default']

        return (
            f"🌟 *{data['name'].capitalize()}*\n"
            f"Типы: {types}\n"
            f"Способности: {abilities}\n"
            f"Рост: {data['height'] / 10} м\n"
            f"Вес: {data['weight'] / 10} кг\n"
            f"[Посмотреть]({image_url})"
        )
    except Exception as e:
        return f"❌ Ошибка при получении информации о покемоне: {e}"


# --- ХЕНДЛЕРЫ (не менялись) ---

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я BotMaster — твой помощник для вдохновения и развлечений!\n\n"
        "Доступные команды:\n"
        "/fact — случайный факт о числе\n"
        "/bored — чем заняться, когда скучно\n"
        "/cat — случайный котик\n"
        "/joke — шутка от папы\n"
        "/pokemon <имя> — информация о покемоне (например, /pokemon pikachu)"
    )


@dp.message(Command("fact"))
async def cmd_fact(message: Message):
    fact_text = get_number_fact()
    await message.answer(fact_text)


@dp.message(Command("bored"))
async def cmd_bored(message: Message):
    activity = get_bored_activity()
    await message.answer(activity, parse_mode="Markdown")


@dp.message(Command("cat"))
async def cmd_cat(message: Message):
    cat_url = get_cat_image()
    if cat_url:
        await message.answer_photo(cat_url)
    else:
        await message.answer("❌ Не удалось получить картинку котика 😿")


@dp.message(Command("joke"))
async def cmd_joke(message: Message):
    joke_text = get_joke()
    await message.answer(joke_text)


@dp.message(Command("pokemon"))
async def cmd_pokemon(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer("❗ Укажи имя покемона. Например: /pokemon pikachu")
        return

    pokemon_name = args[1].strip()
    info = get_pokemon_info(pokemon_name)
    await message.answer(info, parse_mode="Markdown", disable_web_page_preview=False)


# --- ЗАПУСК БОТА ---
async def main():
    logger.info("🤖 Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())