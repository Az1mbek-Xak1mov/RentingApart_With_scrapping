from aiogram.fsm.state import State, StatesGroup

class StepByStepStates(StatesGroup):
    phone = State()
    start = State()
    url = State()