from aiogram.fsm.state import State, StatesGroup


class CinemaStates(StatesGroup):
    waiting_for_search_query = State()
    waiting_for_content_selection = State()
    waiting_for_playback_confirmation = State()
