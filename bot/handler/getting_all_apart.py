import asyncio
import logging
import time
import traceback
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, InputMediaPhoto, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import Session
from aiogram.types import InputMediaPhoto, FSInputFile
from bot.buttons.reply import make_reply_btn
from db.models import Apartment
from db.engine import Base, SessionLocal
from bot.dispatcher import dp
from bot.states import StepByStepStates
import os
from pathlib import Path
from aiogram import F



@dp.message(StepByStepStates.start, F.text == "Getting All Apartment")
async def phone_request_handler(message: Message, state: FSMContext) -> None:
    await message.answer(text='Malumotlar bazasidagi barcha kvartiralar:',reply_markup=ReplyKeyboardRemove())
    session: Session = SessionLocal()
    try:
        # ORM query
        apartments = (
            session.query(Apartment).all()
        )

        if not apartments:
            await message.answer("🚫 Hech qanday uy topilmadi.")
            return

        for apt in apartments:
            text = (
                f"🔑(№ {apt.id})🔑"
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
            if media:
                await message.answer_media_group(media)
            else:
                await message.answer(text, parse_mode="HTML")
            time.sleep(1)

    except Exception as e:
        print("phone_request_handler error:", e)
        traceback.print_exc()
        await message.answer(
            "⚠️ Ma'lumotlar bazasida xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."

        )
    finally:
        session.close()

    # back button
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙Orqaga", callback_data="/start"))
    builder.adjust(1)

    await message.answer("⬅️ Asosiy panelga qaytish", reply_markup=builder.as_markup())
    await state.clear()

@dp.callback_query(F.data=="/start")
async def command_start_handler(call: CallbackQuery, state: FSMContext) -> None:
    btns = ["Getting All Apartment", "Getting Apartment"]
    sizes = [2]
    markup = make_reply_btn(btns, sizes)
    await state.set_state(StepByStepStates.start)
    await call.message.answer("Hush kelibsiz!", reply_markup=ReplyKeyboardRemove())
    await call.message.answer("Faqat tugmalardan foydalaning", reply_markup=markup)
