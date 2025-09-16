import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.markdown import hbold
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


# Команда /help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Вот что я умею:\n"
        "/start — начать работу\n"
        "/help — получить помощь\n"
        "/links — показать кнопки вызова ссылок\n"
        "/dynamic — показать больше опций\n"
        "Если хозяин захочет, я еще что-нибудь сделаю!"
    )

# ========== ЗАДАНИЕ 1: /start с текстовыми кнопками ==========
# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаём клавиатуру с двумя кнопками
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Привет"), KeyboardButton(text="Пока")]
        ],
        resize_keyboard=True,  # Подстраивает размер кнопок под экран
        one_time_keyboard=False  # Кнопки остаются после нажатия
    )

    await message.answer("Выберите действие:", reply_markup=keyboard)


# Обработчик текстовых сообщений (кнопок)
@dp.message(lambda message: message.text in ["Привет", "Пока"])
async def handle_greetings(message: types.Message):
    user_first_name = message.from_user.first_name or "друг"

    if message.text == "Привет":
        await message.answer(f"Привет, <b>{user_first_name}</b>!", parse_mode="HTML")
    elif message.text == "Пока":
        await message.answer(f"До свидания, <b>{user_first_name}</b>!", parse_mode="HTML")


# ========== ЗАДАНИЕ 2: /links с URL-кнопками ==========
@dp.message(Command("links"))
async def cmd_links(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📰 Новости", url="https://news.yandex.ru")],
            [InlineKeyboardButton(text="🎵 Музыка", url="https://music.yandex.ru")],
            [InlineKeyboardButton(text="🎬 Видео", url="https://youtube.com")]
        ]
    )
    await message.answer("Нажмите на кнопку, чтобы перейти по ссылке:", reply_markup=keyboard)


# ========== ЗАДАНИЕ 3: /dynamic — Динамическая клавиатура ==========
@dp.message(Command("dynamic"))
async def cmd_dynamic(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Показать больше опций", callback_data="show_more")]
        ]
    )
    await message.answer("Нажмите кнопку ниже:", reply_markup=keyboard)

# Обработчик: "Показать больше"
@dp.callback_query(lambda c: c.data == "show_more")
async def show_more_options(callback: types.CallbackQuery):
    # Создаём новую клавиатуру
    new_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Опция 1", callback_data="option_1")],
            [InlineKeyboardButton(text="Опция 2", callback_data="option_2")]
        ]
    )

    # Редактируем сообщение: меняем текст и клавиатуру
    await callback.message.edit_text(
        text="Выберите опцию:",
        reply_markup=new_keyboard
    )
    await callback.answer()  # Скрываем "кружок загрузки"

# Обработчики: "Опция 1" и "Опция 2"
@dp.callback_query(lambda c: c.data in ["option_1", "option_2"])
async def handle_option(callback: types.CallbackQuery):
    option = callback.data.replace("option_", "")
    await callback.message.answer(f"Вы выбрали: <b>Опция {option}</b>", parse_mode="HTML")
    await callback.answer()  # Скрываем "кружок загрузки"



# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())