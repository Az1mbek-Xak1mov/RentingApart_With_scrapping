# webscrape/process_olx.py

from sqlalchemy.orm import Session
from db.engine import SessionLocal
from db.models import Apartment, ApartmentImage
from webscrape.olx_utils import parse_parameters, save_image_for_apartment
from webscrape.scrapping_olx import scrape_olx_ad_static

def process_olx_ad(ad_url: str, user_phone: str = None) -> Apartment | None:
    data = scrape_olx_ad_static(ad_url)
    if not data:
        return None

    # unpack
    title       = data.get("Title","")
    description = data.get("Description","")
    price       = data.get("PriceValue")
    images      = data.get("Images",[])
    district    = data.get("Location","")
    seller      = data.get("SellerName")
    map_link    = data.get("MapLink")
    lat         = data.get("Latitude")
    lon         = data.get("Longitude")
    landmark    = data.get("Landmark")

    parsed = parse_parameters(data.get("Parameters",{}))
    if "floor" in parsed and "total_storeys" not in parsed:
        parsed["total_storeys"] = parsed["floor"]

    # required
    miss=[]
    for fld in ("rooms","floor","total_storeys","area"):
        if fld not in parsed: miss.append(fld)
    if miss or price is None or not title or not description:
        print(f"Skipping {ad_url}, missing {miss}")
        return None

    session: Session = SessionLocal()
    try:
        # dedupe by image
        for url in images:
            if session.query(ApartmentImage).filter_by(original_url=url).first():
                return None

        apt = Apartment(
            owner_name   = seller,
            title        = title,
            description  = description,
            price        = price,
            floor        = parsed["floor"],
            total_storeys= parsed["total_storeys"],
            area         = parsed["area"],
            rooms        = parsed["rooms"],
            is_furnished = parsed.get("is_furnished", False),
            district     = district,
            phone_number = user_phone,
            building_type= parsed.get("building_type"),
            repair       = parsed.get("repair"),
            map_link     = map_link,
            latitude     = lat,
            longitude    = lon,
            status       = "active",
            # if you added a `landmark` column, set it here:
            # landmark=landmark
        )
        session.add(apt)
        session.commit()
        apt_id = apt.id

        # save images
        for url in images:
            rp = save_image_for_apartment(apt_id,url)
            if rp:
                img = ApartmentImage(
                    apartment_id = apt_id,
                    original_url = url,
                    local_path   = rp
                )
                session.add(img)
        session.commit()
        return apt

    except Exception as e:
        session.rollback()
        print(f"Error saving {ad_url}: {e}")
        return None

    finally:
        session.close()
