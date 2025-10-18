from os import getenv

from dotenv import load_dotenv

load_dotenv()

class OpenApi:
    OPENAI_API_KEY=getenv('OPENAI_API_KEY')

class Bot:
    TOKEN = getenv("TOKEN")
    ADMIN_CHAT_ID=getenv("ADMIN_CHAT_ID")
class DB:
    DB_NAME = getenv("DB_NAME")
    DB_USER = getenv("DB_USER")
    DB_PASSWORD = getenv("DB_PASSWORD")
    DB_HOST = getenv("DB_HOST")
    DB_PORT = getenv("DB_PORT")

class Web:
    TOKEN = getenv("WEB_TOKEN")

class Payment:
    CLICK_TOKEN = getenv("CLICK_TOKEN")

class Env:
    bot = Bot()
    db = DB()
    web = Web()
    pay = Payment()
    key= OpenApi()
