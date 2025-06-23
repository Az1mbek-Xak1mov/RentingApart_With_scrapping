# RentingApart Bot

A Telegram bot for scraping apartment listings from OLX and serving them to an admin user. This project scrapes apartment data (title, price, area, rooms, floor details, images, etc.) from OLX ads, stores them in a PostgreSQL database, downloads images to a local directory, and allows retrieval via Telegram.

## Features

* Scrape OLX apartment ads statically (title, description, price, parameters, images, location, seller name).
* Optional phone retrieval using Selenium.
* Parse parameters: rooms, floor, total storeys, area, furnishing, building type, repair status.
* Store apartment records in PostgreSQL (`apartments` table).
* Store downloaded images in a directory structure and metadata in `apartment_images` table.
* Telegram bot integration: admin can request apartments by ID or phone number and receive details and images.
* Caches Telegram `file_id` after sending images for faster subsequent sends.

## Requirements

* Python 3.9+
* PostgreSQL server
* ChromeDriver (for Selenium phone scraping, optional)
* A Telegram bot token

## Dependencies

* `sqlalchemy`, `psycopg2-binary` for database ORM
* `python-dotenv` for environment variable loading
* `requests`, `beautifulsoup4` for HTTP scraping
* `selenium` for dynamic phone retrieval (optional)
* `aiogram` (or `python-telegram-bot`) for Telegram bot
* `urllib3`, `re`, `pathlib`, etc.

Install via:

```bash
pip install sqlalchemy psycopg2-binary python-dotenv requests beautifulsoup4 selenium aiogram
```

## Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# Telegram Bot
TOKEN=YOUR_TELEGRAM_BOT_TOKEN
ADMIN_CHAT_ID=YOUR_TELEGRAM_CHAT_ID

# Database (PostgreSQL)
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost          # or your DB host
DB_PORT=5432               # optional; omit or set if needed
DB_NAME=renting_apart

# Image storage directory (optional)
APARTMENT_IMG_DIR=/full/path/to/images  # default: ./images

# Selenium (optional) - if retrieving phone numbers
# Ensure ChromeDriver is installed and in PATH
```

> **Note**: Do not commit `.env` to version control; add it to `.gitignore`.

## Database Setup

1. Ensure PostgreSQL server is running.
2. Create the database. In terminal:

   ```bash
   # Replace user as needed; use superuser or a role with CREATEDB privilege
   psql -h localhost -U postgres
   CREATE DATABASE renting_apart TEMPLATE template0;
   \q
   ```
3. (Optional) Create dedicated DB user:

   ```sql
   CREATE ROLE renting_user WITH LOGIN PASSWORD 'your_password';
   CREATE DATABASE renting_apart OWNER renting_user TEMPLATE template0;
   ```
4. Ensure `.env` has matching `DB_USER`, `DB_PASSWORD`, etc.
5. The application will automatically create tables (`apartments`, `apartment_images`) at startup via SQLAlchemy’s `Base.metadata.create_all(...)` if they do not exist.

## Project Structure

```
project_root/
├── .env
├── main.py            # Telegram bot entrypoint
├── webscrape/
│   ├── main.py        # Scraper entrypoint
│   └── process_olx.py # Scraping logic and DB insertion
├── models/
│   ├── apartment.py
│   └── apartment_image.py
├── db/
│   └── engine.py      # SQLAlchemy engine, Base, SessionLocal
├── olx_utils.py       # parse_parameters, save_image_for_apartment
└── requirements.txt   # optional listing dependencies
```

* **db/engine.py**: Defines `engine`, `SessionLocal`, and `Base = declarative_base()`. Loads environment via `load_dotenv()`.
* **models/**: Contains SQLAlchemy models importing `Base` from `db.engine`.
* **olx\_utils.py**: Helper functions for parsing OLX parameters and saving images locally.
* **webscrape/process\_olx.py**: Contains `process_olx_ad(ad_url, attempt_phone=False)` which:

  1. Scrapes static fields via `requests` + BeautifulSoup.
  2. Parses parameters to fill `rooms`, `floor`, `total_storeys`, `area`, etc.
  3. Checks duplicates by existing `ApartmentImage.original_url`.
  4. Inserts `Apartment` record.
  5. Downloads images into `APARTMENT_IMG_DIR/{apartment_id}/`.
  6. Inserts `ApartmentImage` rows.
* **webscrape/main.py**: Entrypoint to run scraping on a list of URLs.
* **main.py**: Telegram bot startup (using `aiogram`), calls `Base.metadata.create_all(...)`, sets up handlers for admin commands to retrieve apartments.

## Scraper Usage

1. Prepare a list of OLX ad URLs to scrape.
2. In `webscrape/main.py`, import and call `process_olx_ad(url, attempt_phone=False)` in a loop with polite delays (`time.sleep(1-2s)`).
3. Logs indicate skipped ads (missing fields) or inserted IDs.
4. Images are saved under `APARTMENT_IMG_DIR/{id}/uuid.jpg`, and metadata stored in `apartment_images` table.

### Parsing Adjustments

* `parse_parameters` in `olx_utils.py` handles separate keys for `Этаж` and `Этажность дома`, area without suffix, furnishing, building type, repair.
* If an ad omits required fields (`rooms`, `floor`, `total_storeys`, `area`), by default it is skipped. Optionally, fallback logic can be added to assume `total_storeys = floor`.

### Phone Retrieval (Optional)

* `get_phone_with_selenium(ad_url)` uses Selenium + ChromeDriver to click “Show phone”.
* Running Selenium for many ads is resource-intensive; enable only when needed by passing `attempt_phone=True` to `process_olx_ad`.

## Telegram Bot Usage

1. In `main.py`, before starting polling, call:

   ```python
   from db.engine import Base, engine
   import models.apartment, models.apartment_image
   Base.metadata.create_all(bind=engine)
   ```
2. Configure Aiogram handlers (e.g., `/get <apartment_id>` or `/phone <phone_number>`) to query the database:

   ```python
   session = SessionLocal()
   apt = session.query(Apartment).get(apartment_id)
   ```
3. Send apartment details and images:

   * Compose a message with title, price, area, rooms, floor/total, district, furnished, building type, repair, seller name, phone, description snippet.
   * For each `ApartmentImage`: open local file (`APARTMENT_IMG_DIR / img.local_path`) and send via `bot.send_photo`.
   * Optionally cache `telegram_file_id` in `ApartmentImage.telegram_file_id` for faster reuse.

## Error Handling & Logging

* Network errors (requests timeouts) and parsing errors are caught and logged; ads with missing required fields are skipped.
* Database connection errors: ensure `.env` variables are correct and database exists.
* Table creation: import models and call `Base.metadata.create_all(bind=engine)` before any queries.
* In case of collation/template errors when creating DB, use `CREATE DATABASE renting_apart TEMPLATE template0 ...` as needed.

## Deployment

* Ensure environment variables are set in the production environment (or provide a secure `.env`).
* Run the scraper periodically (e.g., via cron) or manually to populate/update listings.
* Run the Telegram bot (e.g., as a systemd service) to listen for admin commands.
* Monitor logs for errors and adjust parsing selectors if OLX structure changes.

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-name`.
3. Make changes, ensure existing functionality remains.
4. Test scraping on sample OLX ads; update `parse_parameters` for new keys/locales as needed.
5. Submit a pull request with clear description.

## License

Specify your license here, e.g., MIT License:

```
MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
...
```

## Disclaimer

* Scraping OLX may violate their terms of service; ensure compliance with site policies and legal regulations. Use polite scraping (rate limiting), and consider using official APIs if available.
* This project is for educational or authorized use only.

---

Thank you for using RentingApart Bot! Feel free to open issues or contribute improvements.
