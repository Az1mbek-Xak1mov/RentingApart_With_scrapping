from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def make_reply_btn(btns, sizes):
    rkb = ReplyKeyboardBuilder()
    rkb.add(*[KeyboardButton(text=text) for text in btns])
    rkb.adjust(*sizes)
    return rkb.as_markup(resize_keyboard=True)