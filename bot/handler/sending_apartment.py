import asyncio
import re
from threading import Event
from typing import Dict, Tuple

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, ReplyKeyboardRemove, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.dispatcher import dp
from bot.states import StepByStepStates
from webscrape import get_all_urls_for_apart


# In-memory registry of running scraping tasks per user
# user_id -> (asyncio.Task, threading.Event)
SCRAPE_TASKS: Dict[int, Tuple[asyncio.Task, Event]] = {}


@dp.message(StepByStepStates.start, F.text == "Sending Link")
async def phone_request_handler(message: Message, state: FSMContext) -> None:
    await message.answer('Send link:' ,reply_markup=ReplyKeyboardRemove())
    await state.set_state(StepByStepStates.url)

@dp.message(StepByStepStates.url, F.text)
async def phone_request_handler(message: Message, state: FSMContext) -> None:
    url = message.text.strip()

    # Basic URL validation
    if not re.match(r"^https?://", url):
        await message.answer("❌ Noto'g'ri link. Iltimos, to'liq URL yuboring (https://...).")
        return

    # Cancel previous task if exists for this user
    prev = SCRAPE_TASKS.pop(message.from_user.id, None)
    if prev:
        task, ev = prev
        ev.set()
        try:
            await asyncio.wait_for(task, timeout=1)
        except Exception:
            pass

    await message.answer('🔎 Scraping boshlandi...')

    # Build inline controls
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="⏹ To'xtatish", callback_data="stop_scraping"),
        InlineKeyboardButton(text="🔙Orqaga", callback_data="/start"),
    )
    builder.adjust(2)
    await message.answer("Scraping jarayoni boshlandi. Istalgan payt to'xtatishingiz mumkin.", reply_markup=builder.as_markup())

    # Launch scraping in a thread; keep cooperative cancel via Event
    stop_event = Event()

    async def run_scrape():
        try:
            await asyncio.to_thread(get_all_urls_for_apart, url, stop_event)
            if not stop_event.is_set():
                await message.answer("✅ Scraping yakunlandi.")
        except Exception:
            # Swallow exceptions to avoid crashing the bot
            await message.answer("⚠️ Scraping vaqtida xatolik yuz berdi, keyinroq urinib ko'ring.")
        finally:
            # Cleanup registry
            SCRAPE_TASKS.pop(message.from_user.id, None)

    task = asyncio.create_task(run_scrape())
    SCRAPE_TASKS[message.from_user.id] = (task, stop_event)

    # Keep state or clear? We'll keep current state so user can resend link if needed
    # await state.clear()


@dp.callback_query(F.data == "stop_scraping")
async def stop_scraping_handler(call: CallbackQuery, state: FSMContext) -> None:
    entry = SCRAPE_TASKS.get(call.from_user.id)
    if not entry:
        await call.answer("Hech qanday jarayon topilmadi.", show_alert=False)
        return

    task, ev = entry
    ev.set()
    try:
        await asyncio.wait_for(task, timeout=2)
    except Exception:
        pass
    finally:
        SCRAPE_TASKS.pop(call.from_user.id, None)

    await call.message.answer("⏹ Scraping to'xtatildi.")
    await call.answer()
