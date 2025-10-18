from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.dispatcher import dp
from bot.states import StepByStepStates
from webscrape import get_all_urls_for_apart


@dp.message(StepByStepStates.start, F.text == "Sending Link")
async def phone_request_handler(message: Message, state: FSMContext) -> None:
    await message.answer('Send link:' ,reply_markup=ReplyKeyboardRemove())
    await state.set_state(StepByStepStates.url)

@dp.message(StepByStepStates.url, F.text)
async def phone_request_handler(message: Message, state: FSMContext) -> None:
    await message.answer('Started scrapping....')
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙Orqaga", callback_data="/start"))
    builder.adjust(1)

    await message.answer("⬅️ Asosiy panelga qaytish", reply_markup=builder.as_markup())
    await state.clear()
    get_all_urls_for_apart(message.text)
