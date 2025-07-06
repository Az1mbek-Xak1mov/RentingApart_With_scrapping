import random
import re
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
from webscrape.process_olx import HEADERS_LIST


def scrape_olx_ad_static(url: str) -> dict:
    """
    Scrapes an OLX ad page. Returns a dict with keys like:
    'Title', 'PriceValue', 'Parameters', 'Description', 'Images', 'Location', 'SellerName',
    and now optionally: 'MapLink', 'Latitude', 'Longitude'.
    """
    session = requests.Session()
    session.headers.update(random.choice(HEADERS_LIST))
    # seed cookies
    session.get("https://www.olx.uz", timeout=5)

    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return {}

    soup = BeautifulSoup(resp.text, 'html.parser')
    data: dict = {}

    # --- existing scraping (Title, PriceValue, Parameters, Description, Images, Location text, SellerName) ---
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
            m = re.search(r'([\d\s]+)', price_text.replace('\u00A0', ' '))
            if m:
                try:
                    data['PriceValue'] = int(m.group(1).replace(' ', ''))
                except:
                    pass

    # Parameters
    params: dict = {}
    container = soup.find('div', attrs={'data-testid': 'ad-parameters-container'})
    if container:
        for p in container.find_all('p'):
            text = p.get_text(strip=True)
            if ':' in text:
                key, val = text.split(':', 1)
                params[key.strip()] = val.strip()
            else:
                params.setdefault('OtherInfo', []).append(text.strip())
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
    for img_container in soup.find_all('div', attrs={'data-testid': 'ad-photo'}):
        img = img_container.find('img')
        if img:
            src = img.get('src') or img.get('data-src')
            if src:
                images.append(urljoin(url, src))
    for img in soup.find_all('img', attrs={'data-testid': re.compile(r'swiper-image')}):
        src = img.get('src') or img.get('data-src')
        if src:
            full = urljoin(url, src)
            if full not in images:
                images.append(full)
    if images:
        data['Images'] = images

    # Location text (district/region)
    location = None
    for p in soup.find_all('p'):
        if p.get_text(strip=True) == 'Местоположение':
            parent = p.find_parent()
            if parent:
                ps = parent.find_all('p')
                vals = [x.get_text(strip=True) for x in ps if x.get_text(strip=True) != 'Местоположение']
                if vals:
                    location = ', '.join(vals)
            break
    if location:
        if "район" in location:
            helper = ''
            index = location.find('район')-2
            while location[index]!=' ' and index!=-1:
                helper+=location[index]
                index-=1
            data['Location'] = helper[::-1]+' район'
        else:
            data['Location'] = location


    # Seller Name
    seller_tag = soup.find(attrs={'data-testid': 'user-profile-user-name'})
    if seller_tag:
        data['SellerName'] = seller_tag.get_text(strip=True)

    # --- NEW: Extract Google Maps link & coordinates ---
    # OLX often has a link like: <a href="https://maps.google.com/maps?ll=41.27051,69.19224&...">Открыть на карте</a>
    map_link = None
    lat = lon = None
    # Find first <a> tag whose href contains maps.google.com/maps?ll=
    a_tag = soup.find('a', href=re.compile(r'maps\.google\.com/maps\?ll='))
    if a_tag:
        print(2)
        href = a_tag.get('href')
        # Make absolute if needed
        map_link = href if href.startswith('http') else urljoin(url, href)
        # Parse lat/lon from query param ll
        try:
            parsed = urlparse(map_link)
            qs = parse_qs(parsed.query)
            ll_vals = qs.get('ll') or qs.get('q')
            if ll_vals:
                parts = ll_vals[0].split(',')
                if len(parts) >= 2:
                    lat = float(parts[0])
                    lon = float(parts[1])
        except Exception as e:
            print(f"Failed parsing map link {map_link}: {e}")

    if map_link:
        data['MapLink'] = map_link
        print(3)
    if lat is not None and lon is not None:
        data['Latitude'] = lat
        data['Longitude'] = lon
        print(4)

    return data
