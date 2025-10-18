import requests
from bs4 import BeautifulSoup
from db.engine import SessionLocal
from db.models import ApartmentUrl
from webscrape.process_olx import process_olx_ad

session = SessionLocal()
def get_all_urls_for_apart(url):
    seen_urls = set()
    for page in range(1, 10):
        url = f"{url}&page={page}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", class_="css-1tqlkj0"):
            href = a.get("href")
            if not href:
                continue
            full_url = "https://www.olx.uz" + href

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


