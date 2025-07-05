import requests
from bs4 import BeautifulSoup
from db.engine import SessionLocal
from db.models import ApartmentUrl
from webscrape.process_olx import process_olx_ad

session = SessionLocal()
def get_all_urls_for_apart(filter_url:str):
    seen_urls = set()
    for page in range(1, 5):
        url = (
            f"{filter_url}&page={page}"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")

        for a in soup.find_all("a", class_="css-1tqlkj0"):
            href = a.get("href")
            if not href:
                continue

            full_url = "https://www.olx.uz" + href

            # Skip if we've already added it in this run:
            if full_url in seen_urls:
                continue

            exists = session.query(
                session.query(ApartmentUrl).filter_by(url=full_url).exists()
            ).scalar()
            if exists:
                continue
            seen_urls.add(full_url)
            session.add(ApartmentUrl(url=full_url, status="new"))
    session.commit()
    session.close()
    return process_olx_ad()


