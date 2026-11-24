from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states import CinemaStates
from search import search_content, CatalogSearchError
from utils import format_content

router = Router()


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
        await message.answer(
            "Önce yayın kaynağını seçmelisin. /Hplay"
        )
        return

    await message.answer("🔎 İçerikler aranıyor...")

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
        await message.answer(
            "Bu aramayla eşleşen içerik bulunamadı."
        )
        return

    await state.update_data(results=results)

    for index, item in enumerate(results[:10], start=1):
        await message.answer(
            f"**{index}. {item['title']}**\n"
            f"{item.get('description', '')[:300]}"
        )

    await message.answer(
        "İçerik sonuçları yukarıda listelendi. "
        "İçerik seçimi özelliğini sonraki dosyada ekleyeceğiz."
    )
