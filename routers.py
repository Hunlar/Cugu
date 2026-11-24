from aiogram import Router

from search_handlers import router as search_router


router = Router(name="group_cinema")

router.include_router(search_router)
