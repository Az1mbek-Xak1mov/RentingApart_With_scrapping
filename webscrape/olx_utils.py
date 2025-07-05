import os
import uuid
from urllib.parse import urlparse
import requests
from pathlib import Path

import re
from decimal import Decimal

def parse_parameters(params: dict) -> dict:
    """
    Given params like {"Количество комнат": "3", "Общая площадь": "85", "Этаж": "7", "Этажность дома": "9", ...},
    return a dict mapping to our model fields:
      - rooms: int
      - floor: int
      - total_storeys: int
      - area: Decimal
      - is_furnished: bool (only if confidently parsed)
      - building_type: str
      - repair: str
    """
    result: dict = {}

    # 1. Rooms: look for key containing "комнат"
    for key, val in params.items():
        if "комнат" in key.lower():
            m = re.search(r"\d+", val)
            if m:
                try:
                    result['rooms'] = int(m.group())
                except:
                    pass
            else:
                # “Студия” → treat as 1
                if "студ" in val.lower():
                    result['rooms'] = 1
            break

    # 2. Floor and total_storeys
    floor = None
    total = None

    # First: combined pattern under a single key, e.g. "Этаж: 3 / 9"
    for key, val in params.items():
        if "этаж" in key.lower() and ("/" in val or "из" in val):
            # Try "3 / 9", "3 из 9", "3/9"
            m = re.search(r"(\d+)\s*(?:/|из)\s*(\d+)", val)
            if m:
                try:
                    floor = int(m.group(1))
                    total = int(m.group(2))
                except:
                    pass
            break

    # Next: if not combined, look separately:
    if floor is None:
        for key, val in params.items():
            # Exactly "Этаж" or contains only "этаж:" but not "этажность"
            if key.lower().strip().startswith("этаж") and "этажность" not in key.lower():
                m = re.search(r"\d+", val)
                if m:
                    try:
                        floor = int(m.group())
                    except:
                        pass
                break

    if total is None:
        for key, val in params.items():
            # Look for "Этажность" (total floors in building)
            if "этажность" in key.lower():
                m = re.search(r"\d+", val)
                if m:
                    try:
                        total = int(m.group())
                    except:
                        pass
                break

    if floor is not None:
        result['floor'] = floor
    if total is not None:
        result['total_storeys'] = total

    # 3. Area: look for key containing "площад"
    for key, val in params.items():
        if "площад" in key.lower():
            # e.g. "85" or "85 м²", "45.5"
            num_part = re.search(r"([\d,.]+)", val.replace(',', '.'))
            if num_part:
                try:
                    result['area'] = Decimal(num_part.group(1))
                except:
                    pass
            break

    # 4. Furnishing: keys like "Меблирована", "Обстановка", "Furnished"
    for key, val in params.items():
        lk = key.lower()
        if any(sub in lk for sub in ["мебел", "обстан", "furnished"]):
            v = val.lower()
            if "без" in v:
                result['is_furnished'] = False
            elif "част" in v:
                result['is_furnished'] = True
            elif any(x in v for x in ["меблирован", "есть мебель", "furnished", "мебель"]):
                result['is_furnished'] = True
            # else leave absent
            break

    # 5. Building type / material: look for "Тип строения", "Тип дома", "Материал"
    for key, val in params.items():
        lk = key.lower()
        # OLX example: "Тип строения: Кирпичный"
        if "тип строен" in lk or "тип дома" in lk or "материал" in lk:
            result['building_type'] = val
            break

    # 6. Repair: key containing "ремонт"
    for key, val in params.items():
        if "ремонт" in key.lower():
            result['repair'] = val
            break

    return result


MAX_IMAGES_PER_APARTMENT = 10

BASE_IMG_DIR = (
    Path(__file__).resolve()
    .parent.parent
    / "webscrape"
    / "images"
)

def save_image_for_apartment(apartment_id: int, image_url: str) -> str | None:
    dirpath = BASE_IMG_DIR / str(apartment_id)
    try:
        dirpath.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Failed to create image directory {dirpath}: {e}")
        return None

    # enforce max images per apartment
    existing = list(dirpath.iterdir())
    if len(existing) >= MAX_IMAGES_PER_APARTMENT:
        # already at (or above) limit
        return None

    # parse extension
    parsed = urlparse(image_url)
    ext = Path(parsed.path).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        ext = ".jpg"

    filename = f"{uuid.uuid4()}{ext}"
    full_path = dirpath / filename

    try:
        resp = requests.get(image_url, timeout=10)
        resp.raise_for_status()
        full_path.write_bytes(resp.content)
        return f"{apartment_id}/{filename}"
    except Exception as e:
        print(f"Failed to download image {image_url}: {e}")
        return None