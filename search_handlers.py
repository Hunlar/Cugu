import logging

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext

from states import CinemaStates
from search import search_content, CatalogSearchError
from utils import format_content

logger = logging.getLogger(__name__)
router = Router()


def results_keyboard(results):
    buttons = []

    for index, item in enumerate(results[:10]):
        buttons.append([
            InlineKeyboardButton(
                text=f"🎬 {item['title'][:50]}",
                callback_data=f"gc_result:{index}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def play_keyboard(index: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="▶️ Sesli sohbette oynat",
            callback_data=f"gc_play:{index}",
        )]
    ])


@router.message(CinemaStates.waiting_for_search_query, F.text)
async def handle_search(
    message: Message,
    state: FSMContext,
    database,
):
    query = message.text.strip()
    data = await state.get_data()
    source = data.get("source")

    if not source:
        await state.clear()
        await message.answer("Önce /Hplay komutuyla kaynak seç.")
        return

    status = await message.answer("🔎 Internet Archive kataloğunda aranıyor...")

    try:
        results = await search_content(
            source=source,
            query=query,
            database=database,
        )
    except CatalogSearchError as exc:
        await status.edit_text(f"Arama hatası: {exc}")
        return

    if not results:
        await status.edit_text(
            "Bu aramada açık lisansı doğrulanmış ve MP4 dosyası bulunan "
            "bir film bulamadım. Başka bir film adı deneyebilirsin."
        )
        return

    await state.update_data(results=results)
    await state.set_state(CinemaStates.waiting_for_content_selection)

    await status.edit_text(
        f"🎬 {len(results)} uygun sonuç bulundu. İzlemek istediğin filmi seç:",
        reply_markup=results_keyboard(results),
    )


@router.callback_query(
    CinemaStates.waiting_for_content_selection,
    F.data.startswith("gc_result:")
)
async def select_result(
    callback: CallbackQuery,
    state: FSMContext,
):
    try:
        index = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("Geçersiz seçim.", show_alert=True)
        return

    data = await state.get_data()
    results = data.get("results", [])

    if index < 0 or index >= len(results):
        await callback.answer("Sonuç artık mevcut değil.", show_alert=True)
        return

    item = results[index]
    details = format_content(item)
    license_label = item.get("license_label") or "Bilinmiyor"
    details += f"\n\n<b>Lisans:</b> {license_label}"

    await callback.message.answer(
        details,
        parse_mode="HTML",
        reply_markup=play_keyboard(index),
    )
    await callback.answer()


@router.callback_query(
    CinemaStates.waiting_for_content_selection,
    F.data.startswith("gc_play:")
)
async def start_playback(
    callback: CallbackQuery,
    state: FSMContext,
    streaming,
    database,
):
    try:
        index = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("Geçersiz seçim.", show_alert=True)
        return

    data = await state.get_data()
    results = data.get("results", [])
    if index < 0 or index >= len(results):
        await callback.answer("Film seçimi bulunamadı. Yeniden ara.", show_alert=True)
        return

    item = results[index]
    media_url = item.get("media_url") or ""

    # Accept only the direct download host created by our Archive provider.
    if not media_url.startswith("https://archive.org/download/"):
        await callback.answer("Geçerli video dosyası bulunamadı.", show_alert=True)
        return

    chat = callback.message.chat
    if chat.type not in ("group", "supergroup"):
        await callback.answer(
            "Oynatma için botu bir Telegram grubunda kullanmalısın.",
            show_alert=True,
        )
        return

    await callback.answer("Yayın başlatılıyor...")
    try:
        await streaming.play(chat_id=chat.id, media_url=media_url)
        await database.save_playback(
            chat_id=chat.id,
            content_id=item["id"],
            position=0,
            status="playing",
            metadata={"source": "internet_archive"},
        )
        await callback.message.answer(
            f"▶️ <b>{item['title']}</b> sesli sohbette başlatıldı.\n"
            "Not: Grubun sesli sohbeti önceden açık olmalı ve yayın hesabı "
            "grupta bulunmalı.",
            parse_mode="HTML",
        )
    except Exception:
        logger.exception("Internet Archive playback failed in chat %s", chat.id)
        await callback.message.answer(
            "Yayın başlatılamadı. Grubun sesli sohbetini açıp yayın hesabının "
            "grupta bulunduğunu kontrol et; ardından yeniden dene."
        )
