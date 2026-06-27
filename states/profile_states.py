from aiogram.fsm.state import State, StatesGroup

class ProfileStates(StatesGroup):
    waiting_for_age = State()
    waiting_for_weight = State()
    waiting_for_height = State()
    waiting_for_goal = State()
    waiting_for_utc = State()