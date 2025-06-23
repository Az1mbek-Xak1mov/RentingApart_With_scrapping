# db/engine.py

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load .env early so environment vars are available
load_dotenv()

# Read environment variables
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT')   # may be None or '' for default
DB_NAME = os.getenv('DB_NAME')

# Validate required vars
missing = []
for var_name, val in [('DB_USER', DB_USER), ('DB_PASSWORD', DB_PASSWORD), ('DB_HOST', DB_HOST), ('DB_NAME', DB_NAME)]:
    if not val:
        missing.append(var_name)
if missing:
    raise RuntimeError(f"Missing required database environment variables: {', '.join(missing)}")

if DB_PORT:
    try:
        int(DB_PORT)
    except ValueError:
        raise RuntimeError(f"Invalid DB_PORT: {DB_PORT!r} is not an integer")
    host_port = f"{DB_HOST}:{DB_PORT}"
else:
    host_port = DB_HOST

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{host_port}/{DB_NAME}"

engine = create_engine(DB_URL, echo=False)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# The Base class for models
Base = declarative_base()
