from bot.handler import *


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())