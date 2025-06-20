from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def make_inline_btn(btns, sizes):
    builder = InlineKeyboardBuilder()
    for text in btns:
        builder.add(InlineKeyboardButton(text=text, callback_data=text))  # important!
    builder.adjust(*sizes)
    return builder.as_markup()
