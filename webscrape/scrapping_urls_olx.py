import requests
from bs4 import BeautifulSoup
from typing import Optional
from threading import Event
from db.engine import SessionLocal
from db.models import ApartmentUrl
from webscrape.process_olx import process_olx_ad


def get_all_urls_for_apart(url: str, stop_event: Optional[Event] = None):
    """
    Scrape listing pages and persist unseen ad URLs.
    Supports cooperative cancellation via stop_event.
    """
    session = SessionLocal()
    try:
        seen_urls = set()
        base_url = url
        for page in range(1, 10):
            if stop_event and stop_event.is_set():
                break

            page_url = f"{base_url}&page={page}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
            }
            try:
                resp = requests.get(page_url, headers=headers, timeout=15)
                resp.raise_for_status()
            except Exception:
                # Skip bad pages but continue the loop
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", class_="css-1tqlkj0"):
                if stop_event and stop_event.is_set():
                    break

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

            # Commit after each page to avoid losing progress on cancellation
            session.commit()

        # Process saved ads (can also be cancelled if supported inside)
        if not (stop_event and stop_event.is_set()):
            return process_olx_ad()
        return None
    finally:
        try:
            session.close()
        except Exception:
            pass


