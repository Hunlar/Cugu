
"""GROUP CINEMA inline keyboard layouts."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎬 Film Ara",
                    callback_data="gc:play"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Destek Grubu",
                    url="https://t.me/ozturkordusu"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Destek Kanalı",
                    url="https://t.me/sancakmain"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👨‍💻 Geliştirici",
                    url="https://t.me/byatillaozturk"
                )
            ]
        ]
    )


def source_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="PuhuTV",
                    callback_data="gc:source:puhutv"
                ),
                InlineKeyboardButton(
                    text="HD Film Cehennemi",
                    callback_data="gc:source:hd_film_cehennemi"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Ana Menü",
                    callback_data="gc:home"
                )
            ]
        ]
    )


def results_keyboard(results):
    buttons = []

    for index, result in enumerate(results[:10]):
        title = result.get("title", "İsimsiz içerik")

        buttons.append([
            InlineKeyboardButton(
                text=f"🎞 {title[:55]}",
                callback_data=f"gc:result:{index}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Geri",
            callback_data="gc:play"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def playback_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶️ Oynat",
                    callback_data="gc:resume"
                ),
                InlineKeyboardButton(
                    text="⏸ Durdur",
                    callback_data="gc:pause"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Baştan Başlat",
                    callback_data="gc:restart"
                ),
                InlineKeyboardButton(
                    text="⏹ Yayını Bitir",
                    callback_data="gc:stop"
                )
            ]
        ]
    )
  
