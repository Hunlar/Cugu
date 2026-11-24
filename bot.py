"""GROUP CINEMA - Telegram bot entry point.

This is the first runnable bot layer: /start, /help and the /Hplay source menu.
Catalog providers, database-backed sessions and actual group-call playback are
added in later project files; this file deliberately does not pretend those
integrations are already implemented.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import settings, validate_bot_config

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("group_cinema")

dp = Dispatcher()

# Tracks the latest menu message per chat for clean menu replacement.
_menu_messages: dict[int, int] = {}


def support_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Destek grubu", url=settings.support_group)],
            [InlineKeyboardButton(text="📢 Destek kanalı", url=settings.support_channel)],
            [InlineKeyboardButton(text="👨‍💻 Geliştirici", url=settings.developer_url)],
            [InlineKeyboardButton(text="🎬 Film ara", callback_data="gc:play")],
        ]
    )


def source_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="PuhuTV", callback_data="gc:source:puhutv"
                ),
                InlineKeyboardButton(
                    text="HD Film Cehennemi",
                    callback_data="gc:source:hd_film_cehennemi",
                ),
            ],
            [InlineKeyboardButton(text="⬅️ Ana menü", callback_data="gc:home")],
        ]
    )


async def replace_menu(message: Message, text: str, reply_markup=None) -> None:
    """Delete the previous bot menu in this chat, then send a fresh one."""
    chat_id = message.chat.id
    previous_id = _menu_messages.get(chat_id)

    if previous_id:
        try:
            await message.bot.delete_message(chat_id, previous_id)
        except Exception:
            logger.debug("Previous menu could not be deleted", exc_info=True)

    sent = await message.answer(text, reply_markup=reply_markup)
    _menu_messages[chat_id] = sent.message_id


async def replace_menu_from_callback(
    callback: CallbackQuery, text: str, reply_markup=None
) -> None:
    if not callback.message:
        await callback.answer()
        return

    chat_id = callback.message.chat.id
    previous_id = _menu_messages.get(chat_id, callback.message.message_id)

    try:
        await callback.bot.delete_message(chat_id, previous_id)
    except Exception:
        logger.debug("Previous menu could not be deleted", exc_info=True)

    sent = await callback.bot.send_message(
        chat_id, text, reply_markup=reply_markup
    )
    _menu_messages[chat_id] = sent.message_id
    await callback.answer()


@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    text = (
        "<b>GROUP CINEMA</b> 🎬\n\n"
        "Grupunuzda sinema deneyimini başlatın.\n"
        "Film aramak için <b>Film ara</b> düğmesine veya /Hplay komutuna basın.\n\n"
        "Yardım için /help komutunu kullanabilirsiniz."
    )
    await replace_menu(message, text, support_keyboard())


@dp.message(Command("help"))
async def help_handler(message: Message) -> None:
    text = (
        "<b>GROUP CINEMA — Yardım</b>\n\n"
        "• /Hplay — Film arama menüsünü açar.\n"
        "• /start — Ana menüyü gösterir.\n"
        "• /help — Yardım bilgisini gösterir.\n\n"
        "Yayın başlatma, yalnızca kullanım hakkı bulunan ve teknik olarak "
        "yetkilendirilmiş yayın kaynakları bağlandığında etkinleştirilecektir."
    )
    await replace_menu(message, text, support_keyboard())


@dp.message(Command("Hplay"))
async def play_handler(message: Message) -> None:
    await replace_menu(
        message,
        "<b>🎬 GROUP CINEMA | Kaynak seç</b>\n\n"
        "Aramak istediğiniz yetkili içerik kaynağını seçin.",
        source_keyboard(),
    )


@dp.callback_query(F.data == "gc:play")
async def play_button_handler(callback: CallbackQuery) -> None:
    await replace_menu_from_callback(
        callback,
        "<b>🎬 GROUP CINEMA | Kaynak seç</b>\n\n"
        "Aramak istediğiniz yetkili içerik kaynağını seçin.",
        source_keyboard(),
    )


@dp.callback_query(F.data == "gc:home")
async def home_button_handler(callback: CallbackQuery) -> None:
    await replace_menu_from_callback(
        callback,
        "<b>GROUP CINEMA</b> 🎬\n\n"
        "Film aramak için aşağıdaki düğmeyi kullanın.",
        support_keyboard(),
    )


@dp.callback_query(F.data.startswith("gc:source:"))
async def source_selected_handler(callback: CallbackQuery) -> None:
    source = callback.data.rsplit(":", 1)[-1]
    source_names = {
        "puhutv": "PuhuTV",
        "hd_film_cehennemi": "HD Film Cehennemi",
    }
    source_name = source_names.get(source)

    if not source_name:
        await callback.answer("Geçersiz kaynak.", show_alert=True)
        return

    # Search provider integration will be connected in a later file.
    await replace_menu_from_callback(
        callback,
        f"<b>{source_name}</b> seçildi.\n\n"
        "Kaynak arama bağlantısı henüz eklenmedi. Sonraki proje dosyalarında, "
        "sağlayıcının izin verdiği resmî erişim yöntemi bağlanacak.",
        source_keyboard(),
    )


async def main() -> None:
    validate_bot_config()
    bot = Bot(token=settings.bot_token, default=None)

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Ana menüyü aç"),
            BotCommand(command="help", description="Yardım"),
            BotCommand(command="Hplay", description="Film ara"),
        ]
    )

    logger.info("GROUP CINEMA bot starting")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
