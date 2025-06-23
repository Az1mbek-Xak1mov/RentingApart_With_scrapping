# process_olx.py
from sqlalchemy.orm import Session
from db.engine import SessionLocal
from db.models import Apartment, ApartmentImage
from webscrape.olx_utils import parse_parameters, save_image_for_apartment
from webscrape.scrapping_olx import scrape_olx_ad_static


def process_olx_ad(ad_url: str, user_phone: str = None) -> Apartment | None:
    data = scrape_olx_ad_static(ad_url)
    if not data:
        print(f"[process_olx_ad] No data scraped from {ad_url}")
        return None

    title = data.get('Title')
    description = data.get('Description')
    price = data.get('PriceValue')
    images = data.get('Images', [])
    location = data.get('Location')
    seller_name = data.get('SellerName')
    params = data.get('Parameters', {})
    parsed = parse_parameters(params)
    if 'floor' in parsed and 'total_storeys' not in parsed:
        parsed['total_storeys'] = parsed['floor']
    missing = []
    if not title: missing.append('title')
    if not description: missing.append('description')
    if price is None: missing.append('price')
    for fld in ('rooms', 'floor', 'total_storeys', 'area'):
        if fld not in parsed:
            missing.append(fld)
    if missing:
        print(f"[process_olx_ad] Skipping {ad_url}: missing fields {missing}")
        return None

    session: Session = SessionLocal()
    try:
        # duplicate check by image URL
        for img_url in images:
            if session.query(ApartmentImage).filter_by(original_url=img_url).first():
                print(f"[process_olx_ad] Duplicate detected, skipping {ad_url}")
                return None

        phone = user_phone
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
            district=location or "",
            phone_number=phone,
            building_type=parsed.get('building_type'),
            repair=parsed.get('repair'),
            status="new",
        )
        session.add(apt)
        session.commit()
        apt_id = apt.id
        for img_url in images:
            rel_path = save_image_for_apartment(apt_id, img_url)
            if rel_path:
                img = ApartmentImage(
                    apartment_id=apt_id,
                    original_url=img_url,
                    local_path=rel_path
                )
                session.add(img)
        session.commit()
        print(f"[process_olx_ad] Inserted Apartment id={apt_id}")
        return apt
    except Exception as e:
        session.rollback()
        print(f"[process_olx_ad] Error saving apartment for {ad_url}: {e}")
        return None
    finally:
        session.close()
