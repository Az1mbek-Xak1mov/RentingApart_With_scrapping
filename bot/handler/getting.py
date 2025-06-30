import os
from pathlib import Path

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder

from sqlalchemy import and_, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from bot.buttons.additional import make_inline_btn_like
from bot.buttons.reply import make_reply_btn
from bot.buttons.inline import make_inline_btn
from bot.dispatcher import dp
from bot.states import StepByStepStates, SearchState

from db.engine import SessionLocal, engine
from db.manager import *

import re


db = SessionLocal()

@dp.message(StepByStepStates.start, F.text == "Getting Apartment")
async def name_handler(message: Message, state: FSMContext):
    await state.set_state(SearchState.district)

    btns = [
        "Алмазарский район", "Бектемирский район", "Мирзо-Улугбекский район",
        "Сергелийский район", "Чиланзарский район", "Шайхантахурский район",
        "Юнусабадский район", "Яккасарайский район", "Яшнабадский район", "Учтепинский район"
    ]
    sizes = [2, 2, 2, 2, 2]
    markup = make_inline_btn(btns, sizes)
    await message.delete()
    await message.answer(
        text="...",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "📍 Qaysi rayondan kvartira kerak:",
        reply_markup=markup
    )


@dp.callback_query(SearchState.district,F.data)
async def name_handler(callback:CallbackQuery,state:FSMContext):
    district=callback.data
    await state.update_data({"district":district})
    await state.set_state(SearchState.rooms)
    btns=[
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
    ]
    sizes=[3,3]
    markup=make_inline_btn(btns,sizes)
    await callback.message.edit_text(
        text="🛏️ Kvartira necha xonali bo'lsin?",
        reply_markup=markup
    )
    await callback.answer()


@dp.callback_query(SearchState.rooms, F.data)
async def name_handler(callback: CallbackQuery, state: FSMContext):
    rooms=callback.data
    await state.update_data({"rooms":rooms})
    await state.set_state(SearchState.start_price)
    await callback.message.edit_text(
        text="💰 Kvartiraning boshlang'ich narxi:",
        reply_markup=None
    )
    await callback.answer()

@dp.message(SearchState.start_price, F.text.isdigit())
async def name_handler(message: Message, state: FSMContext):
    start_price=message.text
    await state.update_data({"start_price":start_price})
    await state.set_state(SearchState.end_price)
    await message.answer(
        text="💵 Kvartiraning oxirgi narxi:",
        reply_markup=None
    )


from aiogram.types import InputMediaPhoto, FSInputFile

@dp.message(SearchState.end_price, F.text.isdigit())
async def price_handler(message: Message, state: FSMContext):
    end_price = int(message.text)
    await state.update_data({"end_price": end_price})
    data = await state.get_data()
    await state.clear()

    required_keys = ["rooms", "district", "start_price", "end_price"]
    if not all(key in data for key in required_keys):
        await message.answer("Iltimos, barcha ma'lumotlarni to'ldiring (xona, tuman, qavat, narx).")
        return

    session: Session = SessionLocal()
    try:
        # ORM query
        apartments = (
            session.query(Apartment)
            .filter_by(rooms=int(data["rooms"]), district=data["district"])
            .filter(Apartment.price > int(data["start_price"]))
            .filter(Apartment.price < end_price)
            .all()
        )

        if not apartments:
            await message.answer("🚫 Hech qanday uy topilmadi.")
            return

        for apt in apartments:
            text = (
                f"📍 Tuman: {apt.district}\n"
                f"🛏️ Xona: {apt.rooms}\n"
                f"🏢 Turi: {apt.building_type or '-'}\n"
                f"🛠️ Remont: {apt.repair or '-'}\n"
                f"📞 Uy egasi raqami: {apt.phone_number or '-'}\n"
                f"🏬 Qavat: {apt.floor}/{apt.total_storeys}\n"
                f"💰 Narx: ${apt.price}\n"
                f"🔗 Manzil: {apt.map_link or '—'}\n"
            )

            # Prepare media group
            media = []
            for idx, img in enumerate(apt.images_list):
                # prefer cached file_id
                if img.telegram_file_id:
                    if idx == 0:
                        media.append(
                            InputMediaPhoto(
                                media=img.telegram_file_id,
                                caption=text,
                                parse_mode="HTML"
                            )
                        )
                    else:
                        media.append(InputMediaPhoto(media=img.telegram_file_id))
                else:
                    # fallback to local file
                    file_path = Path(os.getenv("APARTMENT_IMG_DIR", "images")) / img.local_path
                    if file_path.exists():
                        media.append(
                            InputMediaPhoto(
                                media=FSInputFile(str(file_path)),
                                caption=text if idx == 0 else None,
                                parse_mode="HTML" if idx == 0 else None
                            )
                        )
                    else:
                        continue

            # Send either media group or just text
            if media:
                # answer_media_group will ignore captions after the first
                await message.answer_media_group(media)
            else:
                await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer("⚠️ Ma'lumotlar bazasida xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")
        print("price_handler error:", e)
    finally:
        session.close()

    # back button
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙Orqaga", callback_data="Ijarachi"))
    builder.adjust(1)

    await message.answer("⬅️ Asosiy panelga qaytish", reply_markup=builder.as_markup())
    await state.set_state(StepByStepStates.start)

