import asyncio
import logging
import sys
from os import getenv
from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from bot.buttons.reply import make_reply_btn
from bot.dispatcher import dp
from bot.states import StepByStepStates
from aiogram.filters import CommandStart

@dp.message(F.text=="/start")
async def command_start_handler(message: Message, state: FSMContext) -> None:
    btns = ["Getting All Apartment", "Getting Apartment"]
    sizes = [2]
    markup = make_reply_btn(btns, sizes)
    await state.set_state(StepByStepStates.start)
    await message.answer("Hush kelibsiz!", reply_markup=ReplyKeyboardRemove())
    await message.answer("Faqat tugmalardan foydalaning", reply_markup=markup)
