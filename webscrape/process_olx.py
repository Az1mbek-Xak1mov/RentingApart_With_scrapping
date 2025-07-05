import random
import re
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from db.engine import SessionLocal
from db.models import Apartment, ApartmentImage, ApartmentUrl, AgentPhoneNumber
from webscrape.olx_utils import parse_parameters, save_image_for_apartment
from webscrape.scrapping_olx import scrape_olx_ad_static


HEADERS_LIST = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    },
    {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "X-Requested-With": "XMLHttpRequest",
    },
]
def fetch_olx_phone(ad_url: str) -> str | None:
    session = requests.Session()
    session.headers.update(random.choice(HEADERS_LIST))
    try:
        session.get("https://www.olx.uz/").raise_for_status()
        r = session.get(ad_url)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Skipping {ad_url}, initial request failed: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    span = soup.find("span", class_="css-w85dhy")
    if not span:
        return None

    m = re.search(r"ID:\s*(\d+)", span.text)
    if not m:
        return None
    offer_id = m.group(1)

    # 2) hit the AJAX endpoint
    phone_api = f"https://www.olx.uz/api/v1/offers/{offer_id}/limited-phones/"
    try:
        resp = session.get(phone_api, headers={"Referer": ad_url})
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Skipping {ad_url}, phone API request failed: {e}")
        return None

    phones = resp.json().get("data", {}).get("phones", [])
    if not phones:
        return None

    # 3) normalize: take first phone, strip non-digits
    digits = re.sub(r"\D", "", phones[0])
    if digits.startswith("998") and len(digits) > 9:
        digits = digits[3:]
    return digits if len(digits) == 9 else None



def process_olx_ad() -> Apartment | None:
    session_db = SessionLocal()
    ad_urls = session_db.query(ApartmentUrl).filter_by(status='new').all()
    for ad_url in ad_urls:
        data = scrape_olx_ad_static(ad_url.url)
        if not data:
            print(f"Skipping {ad_url.url}, no data returned")
            ad_url.status = 'done'
            session_db.commit()
            continue

        # fetch phone
        phone = fetch_olx_phone(ad_url.url)
        if not phone:
            print(f"Skipping {ad_url.url}, no phone found")
            return None

        # dedupe by phone
        exists_phone = session_db.query(Apartment).filter_by(phone_number=phone).first()
        agent_phone = session_db.query(AgentPhoneNumber).filter_by(phone_number=phone).first()
        if exists_phone:
            print(f"Skipping {ad_url.url}, phone {phone} already in DB")
            ad_url.status = 'done'
            agent_record = AgentPhoneNumber(
                agent_name=exists_phone.owner_name,
                phone_number=exists_phone.phone_number
            )
            session_db.add(agent_record)
            session_db.query(Apartment).filter(Apartment.phone_number == phone).delete(synchronize_session=False)
            session_db.commit()
            continue

        if agent_phone:
            print(f"Agent phone number :{phone}")
            ad_url.status = 'done'
            continue

        # parse parameters
        parsed = parse_parameters(data.get("Parameters", {}))
        if "floor" in parsed and "total_storeys" not in parsed:
            parsed["total_storeys"] = parsed["floor"]

        missing = [f for f in ("rooms", "floor", "total_storeys", "area") if f not in parsed]
        if missing or data.get("PriceValue") is None or not data.get("Title") or not data.get("Description"):
            print(f"Skipping {ad_url.url}, missing {missing}")
            ad_url.status = 'done'
            session_db.commit()
            continue

        # create apartment record
        apt = Apartment(
            owner_name=data.get("SellerName"),
            title=data.get("Title"),
            description=data.get("Description"),
            price=data.get("PriceValue"),
            floor=parsed["floor"],
            total_storeys=parsed["total_storeys"],
            area=parsed["area"],
            rooms=parsed["rooms"],
            is_furnished=parsed.get("is_furnished", False),
            district=data.get("Location"),
            phone_number=phone,
            building_type=parsed.get("building_type"),
            repair=parsed.get("repair"),
            map_link=data.get("MapLink"),
            latitude=data.get("Latitude"),
            longitude=data.get("Longitude"),
            status="active",
            url_id=ad_url.id
        )
        session_db.add(apt)
        session_db.commit()

        # save images
        for img_url in data.get("Images", []):
            local_path = save_image_for_apartment(apt.id, img_url)
            if local_path:
                session_db.add(ApartmentImage(
                    apartment_id=apt.id,
                    original_url=img_url,
                    local_path=local_path,
                ))
        session_db.commit()

        # mark URL as processed
        ad_url.status = 'done'
        session_db.commit()


    session_db.close()
    return None
