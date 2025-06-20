import asyncio
import logging
import sys
from os import getenv
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.dispatcher import dp


@dp.message()
async def echo_handler(message: Message) -> None:
    await message.answer("Hello")


