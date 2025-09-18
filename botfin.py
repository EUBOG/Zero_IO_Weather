import os
import asyncio
import random

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# import sqlite3
import aiosqlite  # Вместо sqlite3 — асинхронная версия
import aiohttp
import logging
import requests

# Загрузка переменных окружения
load_dotenv()

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализируем бота и диспетчер
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Формируем кнопки
button_consent = KeyboardButton(text="Дать согласие на обработку персональных данных")
button_unconsent = KeyboardButton(text="Отзыв согласия на обработку персональных данных")
button_reg = KeyboardButton(text="Регистрация в телеграм боте")
button_exchange_rates = KeyboardButton(text="Курс валют")
button_tips = KeyboardButton(text="Советы по экономии")
button_finances = KeyboardButton(text="Личные финансы")

keyboards = ReplyKeyboardMarkup(keyboard=[
    [button_consent],
    [button_unconsent],
    [button_reg, button_exchange_rates],
    [button_tips, button_finances]
    ], resize_keyboard=True)

# Инициализация базы данных (асинхронно)
DB_PATH = 'user.db'

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                name TEXT,
                consent_status TEXT DEFAULT 'N',  -- N = нет, Y = да
                consent_date TEXT,
                unconsent_date TEXT,
                category1 TEXT,
                category2 TEXT,
                category3 TEXT,
                expenses1 REAL,
                expenses2 REAL,
                expenses3 REAL
            )
        ''')
        await db.commit()
        logger.info("База данных инициализирована.")

# --- FSM для финансовых данных ---
class FinancesForm(StatesGroup):
    category1 = State()
    expenses1 = State()
    category2 = State()
    expenses2 = State()
    category3 = State()
    expenses3 = State()

# --- Обработчики ---

# Обработчик команды /start
@dp.message(CommandStart())
async def send_start(message: Message):
    await message.answer(
        "Привет! Я ваш личный финансовый помощник.\n\n"
        "Для продолжения работы необходимо:\n"
        "1. Дать согласие на обработку персональных данных.\n"
        "2. Зарегистрироваться (это произойдёт автоматически при согласии).\n\n"
        "В любой момент вы можете отозвать согласие.",
        reply_markup=keyboards
    )

# Обработчик кнопки согласия (сразу и регистрируем пользователя)
@dp.message(F.text == "Дать согласие на обработку персональных данных")
async def consent(message: Message):
    telegram_id = message.from_user.id
    name = message.from_user.full_name or "Пользователь без имени"

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        user = await cursor.fetchone()

        if user:
            if user[3] == "Y":  # consent_status
                await message.answer(f"✅ Ваше согласие было получено: {user[4]}") # Показываем пользователю дату согласия
            else:
                # Обновляем существующего пользователя
                await db.execute(
                    'UPDATE users SET consent_status = ?, consent_date = datetime("now") WHERE telegram_id = ?',
                    ("Y", telegram_id)
                )
                await db.commit()
                await message.answer("✅ Согласие на обработку персональных данных получено!")
        else:
            # Новый пользователь
            await db.execute(
                'INSERT INTO users (telegram_id, name, consent_status, consent_date) VALUES (?, ?, ?, datetime("now"))',
                (telegram_id, name, "Y")
            )
            await db.commit()
            await message.answer("✅ Вы дали согласие на обработку персональных данных и успешно зарегистрированы!")

# Обработчик кнопки отзыва согласия (данные сохраняются с целью фиксации периода действия согласия)
@dp.message(F.text == "Отзыв согласия на обработку персональных данных")
async def unconsent(message: Message):
    telegram_id = message.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        user = await cursor.fetchone()

        if not user:
            await message.answer("❌ Вы не зарегистрированы.")
            return

        if user[3] == "N":
            await message.answer("⚠️ Вы уже отозвали согласие: {user[5]}")
            return

        await db.execute(
            'UPDATE users SET consent_status = ?, unconsent_date = datetime("now") WHERE telegram_id = ?',
            ("N", telegram_id)
        )
        await db.commit()
        await message.answer("🚫 Согласие на обработку персональных данных отозвано. Все данные сохранены в соответствии с законом.")

# Обработчик кнопки регистрации
@dp.message(F.text == "Регистрация в телеграм боте")
async def registration(message: Message):
    telegram_id = message.from_user.id
    name = message.from_user.full_name or "Неизвестный"

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        user = await cursor.fetchone()

        if user:
            if user[3] == "Y":
                await message.answer("✅ Вы уже зарегистрированы и дали согласие!")
            else:
                await message.answer("⚠️ Вы зарегистрированы, но не дали согласие. Нажмите «Дать согласие».")
        else:
            # Регистрируем, но без согласия
            await db.execute(
                'INSERT INTO users (telegram_id, name) VALUES (?, ?)',
                (telegram_id, name)
            )
            await db.commit()
            await message.answer("📌 Вы зарегистрированы, но не дали согласие. Пожалуйста, нажмите «Дать согласие».")


# Обработчик кнопки курса валют
@dp.message(F.text == "Курс валют")
async def exchange_rates(message: Message):
    url = "https://v6.exchangerate-api.com/v6/09edf8b2bb246e1f801cbfba/latest/USD"
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code != 200:
            await message.answer("Не удалось получить данные о курсе валют!")
            return
        usd_to_rub = data['conversion_rates']['RUB']
        eur_to_usd = data['conversion_rates']['EUR']

        euro_to_rub = eur_to_usd * usd_to_rub

        await message.answer(f"1 USD - {usd_to_rub:.2f}  RUB\n"
                             f"1 EUR - {euro_to_rub:.2f}  RUB")


    except:
        await message.answer("Произошла ошибка")

# Формируем пакет советов по экономии
@dp.message(F.text == "Советы по экономии")
async def send_tips(message: Message):
    tips = [
        "Совет 1: Ведите бюджет и следите за своими расходами.",
        "Совет 2: Откладывайте часть доходов на сбережения.",
        "Совет 3: Покупайте товары по скидкам и распродажам.",
        "Совет 4: Ходите в магазин сытым.",
        "Совет 5: К каждому шопингу готовьте список покупок и не покупайте ничего, кроме того, что в списке.",
        "Совет 6: Старайтесь обходиться без кредитов и кредитных карт."
    ]
    tip = random.choice(tips)
    await message.answer(tip)

# Формируем данные по личным финансам
@dp.message(F.text == "Личные финансы")
async def finances(message: Message, state: FSMContext):
    telegram_id = message.from_user.id

    # Сперва проверим, дал ли пользователь согласие на обработку персональных данных
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT consent_status FROM users WHERE telegram_id = ?', (telegram_id,))
        user = await cursor.fetchone()

        if not user or user[0] != "Y":
            await message.answer("⚠️ Сначала дайте согласие на обработку данных!")
            return

    # Если всё ок — начинаем ввод данных
    await state.set_state(FinancesForm.category1)
    await message.answer("Введите первую категорию расходов (например, 'Еда'):")

# Шаг 1: Ввод категории 1
@dp.message(FinancesForm.category1)
async def process_category1(message: Message, state: FSMContext):
    await state.update_data(category1=message.text)
    await state.set_state(FinancesForm.expenses1)
    await message.answer("Введите сумму по этой категории (в рублях):")

# Шаг 2: Ввод суммы 1
@dp.message(FinancesForm.expenses1)
async def process_expenses1(message: Message, state: FSMContext):
    try:
        expenses = float(message.text)
    except ValueError:
        await message.answer("❌ Введите число (например, 500.0)")
        return

    await state.update_data(expenses1=expenses)
    await state.set_state(FinancesForm.category2)
    await message.answer("Введите вторую категорию расходов:")

# Шаг 3: Ввод категории 2
@dp.message(FinancesForm.category2)
async def process_category2(message: Message, state: FSMContext):
    await state.update_data(category2=message.text)
    await state.set_state(FinancesForm.expenses2)
    await message.answer("Введите сумму по этой категории (в рублях):")

# Шаг 4: Ввод суммы 2
@dp.message(FinancesForm.expenses2)
async def process_expenses2(message: Message, state: FSMContext):
    try:
        expenses = float(message.text)
    except ValueError:
        await message.answer("❌ Введите число (например, 500.0)")
        return

    await state.update_data(expenses2=expenses)
    await state.set_state(FinancesForm.category3)
    await message.answer("Введите третью категорию расходов:")

# Шаг 5: Ввод категории 3
@dp.message(FinancesForm.category3)
async def process_category3(message: Message, state: FSMContext):
    await state.update_data(category3=message.text)
    await state.set_state(FinancesForm.expenses3)
    await message.answer("Введите сумму по этой категории (в рублях):")

# Шаг 6: Ввод суммы 3 → Сохранение
@dp.message(FinancesForm.expenses3)
async def process_expenses3(message: Message, state: FSMContext):
    try:
        expenses = float(message.text)
    except ValueError:
        await message.answer("❌ Введите число (например, 500.0)")
        return


    # Получаем все данные из состояния
    data = await state.get_data()
    category1 = data.get("category1")
    expenses1 = data.get("expenses1")
    category2 = data.get("category2")
    expenses2 = data.get("expenses2")
    category3 = data.get("category3")
    expenses3 = expenses  # Только что введённая сумма
    telegram_id = message.from_user.id

    # ✅ АСИНХРОННОЕ ОБНОВЛЕНИЕ В БАЗЕ ДАННЫХ
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE users 
            SET category1 = ?, expenses1 = ?, 
                category2 = ?, expenses2 = ?, 
                category3 = ?, expenses3 = ?
            WHERE telegram_id = ?
        ''', (
            category1, expenses1,
            category2, expenses2,
            category3, expenses3,
            telegram_id
        ))
        await db.commit()  # ✅ Обязательно! Без этого изменения не сохранятся!

    await state.clear()
    await message.answer(
        "✅ Отлично! Ваши данные сохранены:\n\n"
        f"1. {category1}: {expenses1} ₽\n"
        f"2. {category2}: {expenses2} ₽\n"
        f"3. {category3}: {expenses3} ₽"
    )


# --- Запуск ---
async def main():
    await init_db()  # Инициализация БД перед запуском бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())