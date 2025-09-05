import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from googletrans import Translator
from dotenv import load_dotenv
import logging

# Загрузка переменных окружения
load_dotenv()

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Инициализация переводчика
translator = Translator()

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Отправь мне текст, и я переведу его на английский язык.")

# Обработчик текстовых сообщений
@dp.message()
async def translate_message(message: Message):
    if message.text:
        try:
            # Переводим текст на английский (асинхронно)
            translated = await translator.translate(message.text, dest='en')
            await message.answer(f"Перевод на английский:\n{translated.text}")
        except Exception as e:
            await message.answer("Произошла ошибка при переводе. Попробуйте позже.")
            print(f"Ошибка перевода: {e}")  # Для отладки
    else:
        await message.answer("Пожалуйста, отправь текстовое сообщение.")

# Запуск бота
if __name__ == "__main__":
    dp.run_polling(bot)