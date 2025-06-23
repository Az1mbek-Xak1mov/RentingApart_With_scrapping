import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import time

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_olx_ad_static(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SimpleOLXScraper/1.0; +https://example.com/bot-info)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return {}

    soup = BeautifulSoup(resp.text, 'html.parser')
    data = {}

    # Title
    title_tag = soup.find('h1') or soup.select_one('div[data-testid="offer_title"] h4')
    if title_tag:
        data['Title'] = title_tag.get_text(strip=True)

    # Price
    price_container = soup.find('div', attrs={'data-testid': 'ad-price-container'})
    if price_container:
        price_tag = price_container.find('h3')
        if price_tag:
            price_text = price_tag.get_text(strip=True)
            data['PriceText'] = price_text
            m = re.search(r'([\d\s]+)', price_text)
            if m:
                try:
                    data['PriceValue'] = int(m.group(1).replace(' ', ''))
                except ValueError:
                    pass

    params = {}
    container = soup.find('div', attrs={'data-testid': 'ad-parameters-container'})
    if container:
        for p in container.find_all('p'):
            text = p.get_text(strip=True)
            if ':' in text:
                key, val = text.split(':', 1)
                params[key.strip()] = val.strip()
            else:
                params.setdefault('OtherInfo', []).append(text)
    if params:
        data['Parameters'] = params

    # Description
    desc_div = soup.find('div', attrs={'data-testid': 'ad_description'})
    if desc_div:
        inner = desc_div.find('div')
        if inner:
            data['Description'] = inner.get_text(separator=' ', strip=True)

    # Images
    images = []
    # By data-testid="ad-photo"
    for img_container in soup.find_all('div', attrs={'data-testid': 'ad-photo'}):
        img = img_container.find('img')
        if img:
            src = img.get('src') or img.get('data-src')
            if src:
                images.append(urljoin(url, src))
    # Also catch swiper-image variants
    for img in soup.find_all('img', attrs={'data-testid': re.compile(r'swiper-image')}):
        src = img.get('src') or img.get('data-src')
        if src and urljoin(url, src) not in images:
            images.append(urljoin(url, src))
    if images:
        data['Images'] = images

    # Location
    # More precise: OLX snippet shows:
    # <p class="css-7wnksb">Самарканд</p>
    # <p class="css-z0m36u">Самаркандская область</p>
    # under a div data-testid or with preceding <p> “Местоположение”
    loc_div = None
    # Find the section where <p> text == "Местоположение"
    for p in soup.find_all('p'):
        if p.get_text(strip=True) == 'Местоположение':
            # The next sibling container holds two <p> with city and region
            parent = p.find_parent()
            if parent:
                # look inside parent for two <p> tags that are not the header
                ps = parent.find_all('p')
                # filter out the header "Местоположение"
                vals = [x.get_text(strip=True) for x in ps if x.get_text(strip=True) != 'Местоположение']
                if len(vals) >= 1:
                    data['Location'] = ', '.join(vals)
            break

    # Date Posted
    # From snippet:
    # <span class="css-1eaxltp">Опубликовано <span data-cy="ad-posted-at" data-testid="ad-posted-at" class="css-pz2ytp">Сегодня в 01:27</span></span>
    date_span = soup.find(attrs={'data-testid': 'ad-posted-at'})
    if date_span:
        parent = date_span.find_parent()
        if parent:
            txt = parent.get_text(strip=True)
            data['DatePosted'] = txt  # e.g. "Опубликовано Сегодня в 01:27"

    # Seller Name
    seller_tag = soup.find(attrs={'data-testid': 'user-profile-user-name'})
    if seller_tag:
        data['SellerName'] = seller_tag.get_text(strip=True)

    return data

def get_phone_with_selenium(ad_url, timeout=15):
    """
    Uses Selenium to click “Показать телефон” and retrieve the phone number.
    Returns phone string or None.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/114.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(ad_url)
        wait = WebDriverWait(driver, timeout)

        # Wait and click the phone button
        phone_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="ad-contact-phone"]'))
        )
        phone_btn.click()

        # First try: <a href^="tel:">
        try:
            phone_link = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="tel:"]'))
            )
            phone = phone_link.get_attribute('href')
            if phone and phone.lower().startswith('tel:'):
                return phone[4:]
        except:
            pass

        # Second try: button text changes to number inside <span>
        try:
            updated_span = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '[data-testid="ad-contact-phone"] span.n-button-text-wrapper')
                )
            )
            phone_text = updated_span.text.strip()
            m = re.search(r'(\+?\d[\d\s-]{5,}\d)', phone_text)
            if m:
                return m.group(1)
        except:
            pass

        print("Phone did not appear within timeout.")
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    ad_url = "https://www.olx.uz/d/obyavlenie/novza-metro-2-komnata-arenda-ID3Zn4r.html"
    # 1. Scrape static fields
    data = scrape_olx_ad_static(ad_url)
    print("Static data:")
    for k, v in data.items():
        print(f"{k}: {v}")

    # 2. Scrape phone (optional / with caution)
    phone = get_phone_with_selenium(ad_url)
    if phone:
        print("Phone number:", phone)
    else:
        print("Phone number not retrieved.")
