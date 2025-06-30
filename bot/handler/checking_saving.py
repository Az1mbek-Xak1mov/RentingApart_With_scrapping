import asyncio
import logging
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy.orm import Session
import time
from webscrape.process_olx import process_olx_ad
from db.engine import Base
from bot.dispatcher import dp
from bot.states import StepByStepStates
from db.engine import engine
from db.manager import get_phone

from aiogram import F

@dp.message(StepByStepStates.start, F.text == "Adding Apartment")
async def phone_request_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(StepByStepStates.phone)
    await message.answer("Enter phone number:")
    await message.answer("Misol:901234567",reply_markup=ReplyKeyboardRemove())

@dp.message(StepByStepStates.phone, F.text.strip().isdigit())
async def phone_handler(message: Message, state: FSMContext) -> None:
    phone_number = message.text
    # check if phone already in your DB:
    with Session(engine) as session:
        exists = get_phone(session, phone_number)
    if exists:
        await message.answer("Phone number already exists")
        #return that apartment and button for adding one more apartment if owner has more than one
        return
    await state.update_data(phone=phone_number)
    await state.set_state(StepByStepStates.url)
    await message.answer("Enter URL of apartment:")

@dp.message(StepByStepStates.url, F.text)
async def url_handler(message: Message, state: FSMContext) -> None:
    url = message.text.strip()
    data = await state.get_data()
    user_phone = data.get("phone")
    if not user_phone:
        await message.answer("Phone number missing. Please start over with /start.")
        await state.clear()
        return

    await message.answer("Starting to scrape and save apartment. Please wait...")
    loop = asyncio.get_event_loop()
    try:
        apt = await loop.run_in_executor(None, process_olx_ad, url, user_phone)
    except Exception as e:
        logging.exception("Error in process_olx_ad")
        await message.answer(f"Error during scraping: {e}")
        await state.clear()
        return
    if apt:
        await message.answer(f"Apartment saved")
    else:
        await message.answer("Failed to save apartment. Check logs for details.")

    await state.clear()
