from aiogram.fsm.state import State, StatesGroup

class StepByStepStates(StatesGroup):
    phone = State()
    start = State()
    url = State()


class SearchState(StatesGroup):
    district = State()
    start_price = State()
    end_price = State()
    rooms=State()

