import os
import logging
import requests
import urllib.parse
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
import io
from gtts import gTTS
import tempfile
from googletrans import Translator  # Нужно установить: pip install googletrans==4.0.0-rc1
import asyncio


# Загрузка переменных окружения
load_dotenv()

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Инициализация переводчика
translator = Translator()

# OpenWeatherMap API
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}?key={WEATHER_API_KEY}"


# Состояния для FSM
class WeatherStates(StatesGroup):
    waiting_for_city = State()


# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! 👋\nЯ бот прогноза погоды и сохранения фото.\nНапиши /help, чтобы узнать, что я умею.")


# Команда /help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Вот что я умею:\n"
        "/start — начать работу\n"
        "/help — получить помощь\n"
        "/forecast — получить прогноз погоды (введи название города)\n"
        "Также я могу сохранять присланные мне фото в папку IMG и отправлять голосовые соообщения!"
    )


# Команда /forecast
@dp.message(Command("forecast"))
async def cmd_forecast(message: types.Message, state: FSMContext):
    await message.answer("Введите название города:")
    await state.set_state(WeatherStates.waiting_for_city)


# Обработка введённого города
@dp.message(WeatherStates.waiting_for_city)
async def get_weather(message: types.Message, state: FSMContext):
    city = message.text.strip()
    encoded_city = urllib.parse.quote(city)

    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{encoded_city}"
    params = {
        'key': WEATHER_API_KEY,
        'unitGroup': 'metric',
        'include': 'current',  # или 'days'
        'lang': 'ru'
    }

    try:
        response = requests.get(url, params=params)
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text[:300]}...")  # Печатаем начало ответа для отладки

        if response.status_code != 200:
            await message.answer("❌ Ошибка: неверный ключ или город не найден.")
            return

        data = response.json()

        # Извлечение данных
        location = data.get("resolvedAddress", city)
        today = data["days"][0]
        temp = today["temp"]
        desc = today.get("description", today["conditions"])
        humidity = today["humidity"]
        wind = today["windspeed"]

        msg = (
            f"🌍 Местоположение: {location}\n"
            f"🌡 Температура: {temp} °C\n"
            f"☁ Погода: {desc}\n"
            f"💧 Влажность: {humidity}%\n"
            f"💨 Ветер: {wind} км/ч"
        )
        await message.answer(msg)

    except requests.exceptions.RequestException as e:
        await message.answer("📡 Ошибка сети. Попробуйте позже.")
        print("Ошибка сети:", e)
    except ValueError as e:  # JSON decode error
        await message.answer("📄 Получен некорректный ответ от сервера.")
        print("Ошибка JSON:", e)
        print("Текст ответа:", response.text)
    except Exception as e:
        await message.answer("⚠ Неизвестная ошибка.")
        print("Ошибка:", e)
    finally:
        await state.clear()


# Функция для создания голосового сообщения
async def create_voice_message(text: str, lang: str = 'ru') -> io.BytesIO:
    """Создает голосовое сообщение из текста"""
    tts = gTTS(text, lang=lang, slow=False, tld='com' if lang == 'en' else 'ru')

    # Создаем временный файл в памяти
    voice_buffer = io.BytesIO()
    tts.write_to_fp(voice_buffer)
    voice_buffer.seek(0)

    return voice_buffer


# Простая функция перевода (без внешних библиотек)
def simple_translate(text: str) -> str:
    """Простая замена часто используемых слов для демонстрации"""
    translations = {
        "Вы направили мне": "You sent me",
        "Я такое не умею": "I don't know how to do this",
        "Я выполняю команды или сохраняю ваши фото": "I execute commands or save your photos",
        "Привет": "Hello",
        "Пока": "Goodbye",
        "Спасибо": "Thank you",
        "Погода": "Weather",
        "город": "city",
        "температура": "temperature"
    }

    result = text
    for ru, en in translations.items():
        result = result.replace(ru, en)

    return result


# Обработка фото от пользователя
@dp.message(lambda message: message.photo)
async def handle_photo(message: types.Message):
    # Создаем папку IMG, если её нет
    if not os.path.exists("IMG"):
        os.makedirs("IMG")
        logging.info("Создана папка IMG")

    # Получаем file_id самого большого фото (с наибольшим размером)
    photo = message.photo[-1]
    file_id = photo.file_id

    # Получаем путь к файлу на серверах Telegram
    file = await bot.get_file(file_id)
    file_path = file.file_path

    # Формируем имя файла
    file_extension = file_path.split('.')[-1]
    file_name = f"IMG/photo_{file_id}.{file_extension}"

    # Скачиваем и сохраняем фото
    await bot.download_file(file_path, file_name)

    await message.answer(f"✅ Фото сохранено как: {file_name}")


# Обработка голосовых сообщений от пользователя
@dp.message(lambda message: message.voice)
async def handle_voice(message: types.Message):
    await message.answer("🎙 Я получил ваше голосовое сообщение! Но пока не умею его обрабатывать.")


# Обработка текстовых сообщений с переводом
@dp.message(lambda message: message.text and not message.text.startswith('/'))
async def handle_text(message: types.Message):
    user_text = message.text

    try:
        # Простой перевод текста (без внешних библиотек)
        english_text = simple_translate(user_text)

        # Создаем русский ответ
        russian_response = f"Вы направили мне {user_text}. Я такое не умею. Я выполняю команды или сохраняю ваши фото."

        # Создаем английский ответ
        english_response = f"You sent me {english_text}. I don't know how to do this. I execute commands or save your photos."

        # Отправляем русское голосовое сообщение
        voice_buffer_ru = await create_voice_message(russian_response, 'ru')
        await message.answer_voice(
            types.BufferedInputFile(voice_buffer_ru.read(), filename="voice_message_ru.mp3"),
            caption=f"Вы сказали: {user_text}"
        )

        # Отправляем английское голосовое сообщение
        voice_buffer_en = await create_voice_message(english_response, 'en')
        await message.answer_voice(
            types.BufferedInputFile(voice_buffer_en.read(), filename="voice_message_en.mp3"),
            caption=f"English: {english_response}"
        )

    except Exception as e:
        # Если возникла ошибка, отправляем простой текстовый ответ
        await message.answer("Извините, произошла ошибка при обработке вашего сообщения.")
        logging.error(f"Ошибка при обработке текста: {e}")


# Обработка любых других сообщений (которые не попали в другие хендлеры)
@dp.message()
async def echo(message: types.Message):
    # Этот хендлер будет обрабатывать все остальные сообщения,
    # которые не попали в предыдущие хендлеры (например, стикеры, документы и т.д.)
    text_response = "Я не понимаю это сообщение. Используйте команды /start, /help или /forecast"

    try:
        # Попробуем отправить голосовое сообщение
        voice_buffer = await create_voice_message(text_response)
        await message.answer_voice(
            types.BufferedInputFile(voice_buffer.read(), filename="voice_message.mp3"),
            caption="Не понимаю это сообщение"
        )
    except Exception as e:
        # Если не удалось создать голосовое сообщение, отправляем текст
        await message.answer(text_response)
        logging.error(f"Ошибка при создании голосового сообщения: {e}")


# Запуск бота
if __name__ == "__main__":
    print("Бот запущен...")
    dp.run_polling(bot)