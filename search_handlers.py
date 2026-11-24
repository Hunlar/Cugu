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

    await message.answer("🔎 Aranıyor...")

    try:
        results = await search_content(
            source=source,
            query=query,
            database=database,
        )
    except CatalogSearchError as exc:
        await message.answer(f"Arama hatası: {exc}")
        return

    if not results:
        await message.answer("İçerik bulunamadı.")
        return

    await state.update_data(results=results)
    await state.set_state(
        CinemaStates.waiting_for_content_selection
    )

    await message.answer(
        f"🎬 {len(results)} sonuç bulundu.\n"
        "İzlemek istediğin içeriği seç:",
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

    await callback.message.answer(
        format_content(item),
        parse_mode="HTML",
    )

    await callback.answer()
