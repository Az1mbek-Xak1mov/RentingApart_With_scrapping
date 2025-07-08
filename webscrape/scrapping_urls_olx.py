import requests
from bs4 import BeautifulSoup
from db.engine import SessionLocal
from db.models import ApartmentUrl
from webscrape.process_olx import process_olx_ad

session = SessionLocal()
def get_all_urls_for_apart():
    seen_urls = set()
    print(1)
    for page in range(1, 3):
        print(2)
        url = (
            f"https://www.olx.uz/nedvizhimost/kvartiry/arenda-dolgosrochnaya/?currency=UYE&search%5Bfilter_float_price:from%5D=600&search%5Bfilter_float_price:to%5D=900&search%5Bfilter_float_number_of_rooms:from%5D=2&search%5Bfilter_float_number_of_rooms:to%5D=3&search%5Bfilter_enum_furnished%5D%5B0%5D=yes&search%5Bfilter_enum_comission%5D%5B0%5D=no&page={page}"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        print(url)
        resp = requests.get(url)
        print(resp)
        soup = BeautifulSoup(resp.text, "html.parser")
        print(soup)
        for a in soup.find_all("a", class_="css-1tqlkj0"):
            print(3)
            href = a.get("href")
            if not href:
                continue

            full_url = "https://www.olx.uz" + href

            # Skip if we've already added it in this run:
            if full_url in seen_urls:
                print(4)
                continue

            exists = session.query(
                session.query(ApartmentUrl).filter_by(url=full_url).exists()
            ).scalar()
            if exists:
                print(5)
                continue
            seen_urls.add(full_url)
            print(6)
            session.add(ApartmentUrl(url=full_url, status="new"))
    session.commit()
    session.close()
    # return process_olx_ad()


