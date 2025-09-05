import os
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
import urllib.parse

# Загрузка переменных окружения
load_dotenv()

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# OpenWeatherMap API
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}?key={WEATHER_API_KEY}"


# Состояния для FSM
class WeatherStates(StatesGroup):
    waiting_for_city = State()


# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! 👋\nЯ бот для получения прогноза погоды.\nНапиши /help, чтобы узнать, что я умею.")


# Команда /help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Вот что я умею:\n"
        "/start — начать работу\n"
        "/help — получить помощь\n"
        "/forecast — получить прогноз погоды (введи название города)"
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


# Запуск бота
if __name__ == "__main__":
    print("Бот запущен...")
    dp.run_polling(bot)