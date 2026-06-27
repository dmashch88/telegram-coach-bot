from aiogram.fsm.state import State, StatesGroup

class GoalStates(StatesGroup):
    waiting_for_goal = State()
    waiting_for_timezone = State()