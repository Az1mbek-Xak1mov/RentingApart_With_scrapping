# RentingApart Bot

A Telegram bot for scraping apartment listings from OLX and serving them to an admin user. This project scrapes apartment data (title, price, area, rooms, floor details, images, location, seller name) from OLX ads, stores them in a PostgreSQL database, downloads images to a local directory, and allows retrieval via Telegram.

## Features

* Scrape OLX apartment ads statically (title, description, price, parameters, images, location, seller name).
* Optional phone retrieval using Selenium.
* Parse parameters: rooms, floor, total storeys, area, furnishing, building type, repair status.
* Store apartment records in PostgreSQL (`apartments` table).
* Store downloaded images in a directory structure and metadata in `apartment_images` table.
* Store location details (address components, latitude, longitude, map link) in a dedicated `locations` table.
* Telegram bot integration: admin can request apartments by ID or phone number and receive details, images, and location pins or map links.
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
5. The application will automatically create tables (`apartments`, `apartment_images`, `locations`) at startup via SQLAlchemy’s `Base.metadata.create_all(...)` if they do not exist.

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
│   ├── apartment_image.py
│   └── location.py    # new Location model
├── db/
│   └── engine.py      # SQLAlchemy engine, Base, SessionLocal
├── olx_utils.py       # parse_parameters, save_image_for_apartment, extract location
└── requirements.txt   # optional listing dependencies
```

* **db/engine.py**: Defines `engine`, `SessionLocal`, and `Base = declarative_base()`. Loads environment via `load_dotenv()`.
* **models/**: Contains SQLAlchemy models importing `Base` from `db.engine`. Now includes:

  * `Apartment`: main listing data
  * `ApartmentImage`: images metadata
  * `Location`: address components + latitude/longitude + map link
* **olx\_utils.py**: Helper functions for parsing OLX parameters, saving images locally, extracting location data (map link and coordinates).
* **webscrape/process\_olx.py**: Contains `process_olx_ad(ad_url, attempt_phone=False)` which:

  1. Scrapes static fields via `requests` + BeautifulSoup.
  2. Parses parameters to fill `rooms`, `floor`, `total_storeys`, `area`, etc.
  3. Extracts location: city/district text and Google Maps link + lat/lon.
  4. Checks duplicates by existing `ApartmentImage.original_url`.
  5. Inserts `Apartment` record.
  6. Downloads images into `APARTMENT_IMG_DIR/{apartment_id}/`.
  7. Inserts `ApartmentImage` rows.
  8. Inserts `Location` row linked to the `Apartment`.
* **webscrape/main.py**: Entrypoint to run scraping on a list of URLs.
* **main.py**: Telegram bot startup (using `aiogram`), calls `Base.metadata.create_all(...)`, sets up handlers for admin commands to retrieve apartments.

## Models

### Apartment (models/apartment.py)

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BIGINT, String, Text, Integer, DECIMAL, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from decimal import Decimal
from db.engine import Base

class Apartment(Base):
    __tablename__ = "apartments"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    owner_name: Mapped[str] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    floor: Mapped[int] = mapped_column(Integer, nullable=False)
    total_storeys: Mapped[int] = mapped_column(Integer, nullable=False)
    area: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    rooms: Mapped[int] = mapped_column(Integer, nullable=False)
    is_furnished: Mapped[bool] = mapped_column(Boolean, nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=True)
    building_type: Mapped[str] = mapped_column(String(50), nullable=True)
    repair: Mapped[str] = mapped_column(String(50), nullable=True)
    # New location fields
    map_link: Mapped[str] = mapped_column(String(500), nullable=True)
    latitude: Mapped[Decimal] = mapped_column(DECIMAL(9, 6), nullable=True)
    longitude: Mapped[Decimal] = mapped_column(DECIMAL(9, 6), nullable=True)

    scraped_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    status: Mapped[str] = mapped_column(String(50), nullable=True)

    images_list = relationship(
        "ApartmentImage",
        back_populates="apartment",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<Apartment(id={self.id}, title={self.title!r}, price={self.price}, "
            f"area={self.area}, rooms={self.rooms}, floor={self.floor}/{self.total_storeys})>"
        )
```

### ApartmentImage (models/apartment\_image.py)

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BIGINT, String, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from db.engine import Base

class ApartmentImage(Base):
    __tablename__ = "apartment_images"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    apartment_id: Mapped[int] = mapped_column(
        BIGINT, ForeignKey("apartments.id", ondelete="CASCADE"), nullable=False
    )
    original_url: Mapped[str] = mapped_column(String(500), nullable=True)
    local_path: Mapped[str] = mapped_column(String(500), nullable=False)
    telegram_file_id: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    apartment = relationship("Apartment", back_populates="images_list")

    def __repr__(self):
        return f"<ApartmentImage(id={self.id}, apartment_id={self.apartment_id}, local_path={self.local_path})>"
```

## olx\_utils.py updates

* **parse\_parameters**: handles rooms, floor, total\_storeys, area, furnishing, building type, repair.
* **save\_image\_for\_apartment**: downloads and stores images.
* **extract location**: in `scrape_olx_ad_static`, find Google Maps link and parse `ll` parameter for latitude/longitude:

```python
# inside scrape_olx_ad_static
# ... after other fields ...
map_link = None
lat = lon = None
# Find first <a> with maps link
a_tag = soup.find('a', href=re.compile(r'maps\.google\.com/maps\?ll='))
if a_tag:
    href = a_tag.get('href')
    map_link = href if href.startswith('http') else urljoin(url, href)
    try:
        parsed = urlparse(map_link)
        qs = parse_qs(parsed.query)
        ll_vals = qs.get('ll') or qs.get('q')
        if ll_vals:
            parts = ll_vals[0].split(',')
            lat, lon = float(parts[0]), float(parts[1])
    except:
        pass

if map_link:
    data['MapLink'] = map_link
if lat is not None and lon is not None:
    data['Latitude'] = lat
    data['Longitude'] = lon
```

## process\_olx\_ad updates

In `webscrape/process_olx.py`, after scraping and parsing, set the new location columns on the `Apartment` before commit:

```python
    apt = Apartment(
        owner_name=seller_name,
        title=title,
        description=description,
        price=price,
        floor=parsed['floor'],
        total_storeys=parsed['total_storeys'],
        area=parsed['area'],
        rooms=parsed['rooms'],
        is_furnished=parsed.get('is_furnished', False),
        district=location_text or "",
        phone_number=phone,
        building_type=parsed.get('building_type'),
        repair=parsed.get('repair'),
        status="new",
        map_link=data.get('MapLink'),
        latitude=data.get('Latitude'),
        longitude=data.get('Longitude'),
    )
```

## Telegram Bot: sending location

When you fetch an `Apartment`, send a location pin if `latitude` and `longitude` exist:

```python
if apartment.latitude and apartment.longitude:
    await bot.send_location(
        chat_id=chat_id,
        latitude=float(apartment.latitude),
        longitude=float(apartment.longitude)
    )
elif apartment.map_link:
    await bot.send_message(chat_id=chat_id, text=f"📍 Ссылка на карту: {apartment.map_link}")
```

## Table creation

Ensure at startup you import models and call:

```python
from db.engine import Base, engine
import models.apartment, models.apartment_image
Base.metadata.create_all(bind=engine)
```

so the new `map_link`, `latitude`, and `longitude` columns are created.

---

With these changes, your `Apartment` model now directly stores location data in dedicated columns, enabling the bot to send exact map pins or links in Telegram without embedding them in the description.
