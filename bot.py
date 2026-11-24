import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import settings, validate_bot_config, validate_streaming_config
from states import CinemaStates
from routers import router
from storage import initialize_storage, close_storage
from middlewares import CinemaMiddleware
from telegram_client import TelegramUserClient
from streaming import StreamingManager


logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("group_cinema")


def source_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📺 PuhuTV", callback_data="gc_source:puhutv")],
        [InlineKeyboardButton(text="🎬 HD Film Cehennemi", callback_data="gc_source:hd_film_cehennemi")],
    ])


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Film / Dizi Ara", callback_data="gc_menu:play")],
        [InlineKeyboardButton(text="❓ Yardım", callback_data="gc_menu:help")],
        [InlineKeyboardButton(text="💬 Destek", url=settings.support_group)],
    ])


async def start_handler(message: Message):
    await message.answer(
        "🎬 <b>GROUP CINEMA</b>\n\nGrubunda film ve dizi aramak için aşağıdaki butonu kullanabilirsin.",
        reply_markup=main_menu(),
    )


async def help_handler(message: Message):
    await message.answer(
        "🎬 <b>GROUP CINEMA YARDIM</b>\n\n"
        "/start - Ana menü\n/help - Yardım\n/Hplay - Film veya dizi ara\n\n"
        f"Destek: {settings.support_group}"
    )


async def play_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Yayın kaynağını seç:", reply_markup=source_menu())


async def source_handler(callback: CallbackQuery, state: FSMContext):
    source = callback.data.split(":", 1)[1]
    if source not in ("puhutv", "hd_film_cehennemi"):
        await callback.answer("Geçersiz kaynak.", show_alert=True)
        return
    await state.update_data(source=source)
    await state.set_state(CinemaStates.waiting_for_search_query)
    await callback.message.answer("🔎 Aramak istediğin film veya dizinin adını yaz:")
    await callback.answer()


async def menu_handler(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":", 1)[1]
    if action == "play":
        await state.clear()
        await callback.message.answer("Yayın kaynağını seç:", reply_markup=source_menu())
    elif action == "help":
        await callback.message.answer("/start - Ana menü\n/help - Yardım\n/Hplay - Film veya dizi ara")
    await callback.answer()


async def main():
    validate_bot_config()
    validate_streaming_config()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(CinemaMiddleware())
    dp.include_router(router)

    dp.message.register(start_handler, Command("start"))
    dp.message.register(help_handler, Command("help"))
    dp.message.register(play_handler, Command("Hplay"))
    dp.callback_query.register(source_handler, F.data.startswith("gc_source:"))
    dp.callback_query.register(menu_handler, F.data.startswith("gc_menu:"))

    user_client = TelegramUserClient()
    streaming = None
    user_started = False
    storage_started = False

    try:
        mtproto_client = await user_client.start()
        user_started = True

        streaming = StreamingManager(mtproto_client)
        await streaming.start()
        dp["streaming"] = streaming
        logger.info("Telegram kullanıcı hesabı ve PyTgCalls başlatıldı.")

        await initialize_storage()
        storage_started = True
        logger.info("PostgreSQL bağlantısı hazır.")

        await dp.start_polling(bot)

    finally:
        if storage_started:
            await close_storage()
        if streaming is not None:
            try:
                await streaming.calls.stop()
            except Exception:
                logger.exception("PyTgCalls kapatılırken hata oluştu.")
        if user_started:
            await user_client.stop()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
