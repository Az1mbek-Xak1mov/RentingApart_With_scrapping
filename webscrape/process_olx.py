import random
import re
import requests
from bs4 import BeautifulSoup
from db.engine import SessionLocal
from db.models import Apartment, ApartmentImage, ApartmentUrl, AgentPhoneNumber
from environment.utils import Env
from webscrape.olx_utils import parse_parameters, save_image_for_apartment
from webscrape.scrapping_olx import scrape_olx_ad_static
from typing import Optional
from openai import OpenAI
key = Env.key.OPENAI_API_KEY

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
    processed_count = 0
    ad_urls = session_db.query(ApartmentUrl).filter_by(status='new').all()
    for ad_url in ad_urls:
        data = scrape_olx_ad_static(ad_url.url)
        if not data:
            print(f"Skipping {ad_url.url}, no data returned")
            ad_url.status = 'done'
            session_db.commit()
            continue

        phone = fetch_olx_phone(ad_url.url)

        parsed = parse_parameters(data.get("Parameters", {}))
        if "floor" in parsed and "total_storeys" not in parsed:
            parsed["total_storeys"] = parsed["floor"]

        missing = [f for f in ("rooms", "floor", "total_storeys", "area") if f not in parsed]
        if missing or data.get("PriceValue") is None or not data.get("Title") or not data.get("Description"):
            print(f"Skipping {ad_url.url}, missing {missing}")
            ad_url.status = 'done'
            session_db.commit()
            continue

        def extract_address_llm(description: str) -> Optional[str]:
            api_key = key
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY environment variable not set")

            # 2. Instantiate the client
            client = OpenAI(api_key=api_key)

            # 3. Build the prompt
            system_prompt = (
                "You are a strict address extractor for short property rental ads.\n"
                "RULES (priority & behavior):\n"
                "1) Extract ONLY the single best address/location from the ad and NOTHING else.\n"
                "2) Prefer more specific actionable locations in this order (highest -> lowest):\n"
                "   a) street + number (e.g., 'ул. Лермонтова 5')\n"
                "   b) landmark with qualifier or direction/distance (e.g., '3 остановки от м. Дустлик', 'за Сезам', 'рядом с больница Жуковский')\n"
                "   c) metro name (e.g., 'м. Дустлик', 'Метро: Янгиҳаёт')\n"
                "   d) массив/массив + number (e.g., 'Чилонзор 18 массив')\n"
                "   e) район/туман only as a last resort.\n"
                "3) IMPORTANT: If the ad contains a district/район/туман/масcив **only** and no more specific location (no street, no landmark, no metro/distance), RETURN the string 'null' (lowercase) — do NOT return the generic district as the address.\n"
                "4) If both a generic region and a more specific cue exist, return the MORE SPECIFIC cue (e.g., if text has 'Яшнабадский район' and '3 остановки от м. Дустлик', return '3 остановки от м. Дустлик').\n"
                "5) Normalize to Russian/Cyrillic — transliterate Latin-script Uzbek/English to Russian phonetics when needed (e.g., 'Yangihayot' -> 'Янгиҳаёт', 'sezam' -> 'Сезам').\n"
                "6) Capitalize appropriately (e.g., 'Больница Жуковский', 'Метрo: Янгиҳаёт').\n"
                "7) Output EXACTLY one string — the address text alone (no JSON, no quotes, no punctuation wrappers). If no appropriate address is found, output the literal string: null\n"
                "8) Do NOT output any explanation, extra text, or other fields — only a single line containing the address or 'null'.\n"
                "\n"
                "EXAMPLES (input -> output):\n"
                "Input:\n"
                "Xamma waroilari bn yangi remontdan ciqqan ... yunusobod 4kv da kvartira  sezam orqasida joylawgan\n"
                "Output:\n"
                "Сезам, сзади\n"
                "\n"
                "Input:\n"
                "Chilonzor 18 mavzeda Arendaga kvartira qizlarga. 2 ta qiz kerak ...\n"
                "Output:\n"
                "Чилонзор 18 массив\n"
                "\n"
                "Input:\n"
                "Предлагается ... в центре на Ц - 6, ориентир Юнус-Абадская налоговая. ...\n"
                "Output:\n"
                "Юнус-Абадская налоговая\n"
                "\n"
                "Input:\n"
                "Предложение только для иностранных граждан. ... в Яшнабадском районе, 3 остановки от м. Дустлик. ...\n"
                "Output:\n"
                "3 остановки от м. Дустлик\n"
                "\n"
                "Input:\n"
                "Уютная квартира, рядом школа и парк. Без точного адреса, подробности в Telegram.\n"
                "Output:\n"
                "null\n"
            )

            user_prompt = (
                "Extract the single best address/location from the following advertisement.\n\n"
                f"---\n{description.strip()}\n---\n\n"
                "Return EXACTLY one string."
            )

            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content":user_prompt}
                ],
                temperature=0.0,
                max_tokens=20,
            )

            text = resp.choices[0].message.content.strip().strip('"')
            return None if text.lower() in ("null", "none") else text
        address=extract_address_llm(data.get("Description"))
        print(address)
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
            map_link=address,
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
        processed_count += 1


    session_db.close()
    return processed_count
