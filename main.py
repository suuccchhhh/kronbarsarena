import asyncio, logging, os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo,
    CallbackQuery
)
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

logging.basicConfig(level=logging.INFO)
dp = Dispatcher()

# Укажите идентификатор канала:
# Для публичного канала можно использовать @username, но надежнее -100... ID.
# Работает и так, и так, если бот — админ канала.
CHANNEL_ID = "@KronBarsArena"   # или числовой id вида -1001234567890
CHANNEL_URL = "https://t.me/KronBarsArena"

def webapp_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Открыть Бронирование", web_app=WebAppInfo(url=WEBAPP_URL))
    ]])

def check_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти в канал", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="Проверить подписку", callback_data="check_sub")]
    ])

async def is_subscribed(bot: Bot, user_id: int) -> bool:
    """
    Проверяем подписку через get_chat_member.
    Подписан, если статус один из: member/administrator/creator.
    """
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        # В aiogram v3 статусы – это Enum; используем .status.value
        status = getattr(member, "status", None)
        status_value = getattr(status, "value", str(status))
        return status_value in ("member", "administrator", "creator")
    except Exception as e:
        # Например, если бот не админ канала / нет доступа
        logging.warning(f"get_chat_member error for user {user_id}: {e}")
        return False

@dp.message(CommandStart())
async def start(m: Message):
    text = (
        "Привет! Чтобы открыть бронирование, сначала подпишись на канал KronBarsArena:\n"
        f"{CHANNEL_URL}\n\n"
        "Когда подпишешься — нажми «Проверить подписку» ниже 👇"
    )
    await m.answer(text, reply_markup=check_kb())

@dp.callback_query(F.data == "check_sub")
async def on_check_sub(cb: CallbackQuery):
    user_id = cb.from_user.id
    ok = await is_subscribed(cb.message.bot, user_id)
    if ok:
        await cb.message.answer(
            "✅ Подписка найдена! Открывай мини-приложение для бронирования:",
            reply_markup=webapp_kb()
        )
    else:
        await cb.message.answer(
            "❌ Подписка не обнаружена. Перейди в канал, подпишись и заново нажми «Проверить подписку».",
            reply_markup=check_kb()
        )
    await cb.answer()  # закрыть «часики» на кнопке

@dp.message(Command("webapp"))
async def open_webapp(m: Message):
    # Доп. команда: откроет веб-апп, но можно и тут проверять подписку при желании
    await m.answer("Лови кнопку:", reply_markup=webapp_kb())

@dp.message(F.text)
async def fallback(m: Message):
    await m.answer("Напиши /start, чтобы проверить подписку, или /webapp — чтобы открыть мини-приложение.")

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env")
    if not (WEBAPP_URL and WEBAPP_URL.startswith("https://")):
        raise RuntimeError("WEBAPP_URL must be HTTPS (Telegram требует TLS).")
    bot = Bot(BOT_TOKEN)
    logging.info("Bot is starting…")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
