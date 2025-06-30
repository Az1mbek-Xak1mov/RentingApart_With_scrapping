# webscrape/scrapping_olx.py

import re
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

from webscrape.olx_ai import redact_phone, extract_landmark, translate

def scrape_olx_ad_static(url: str) -> dict:
    """
    Scrapes an OLX ad page, then:
      1. Redacts phone numbers
      2. Extracts a landmark if no real map_link
      3. Translates into Russian
    Returns a dict with keys:
    Title, PriceValue, Parameters, Description, Images, Location, SellerName,
    MapLink, Latitude, Longitude, Landmark (optional).
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return {}
    soup = BeautifulSoup(resp.text, "html.parser")
    data = {}

    # --- Basic scrape ---
    # Title
    t = soup.find("h1") or soup.select_one('div[data-testid="offer_title"] h4')
    data["Title"] = t.get_text(strip=True) if t else ""

    # Price
    pc = soup.find("div", attrs={"data-testid": "ad-price-container"})
    if pc and (p:=pc.find("h3")):
        m = re.search(r"([\d\s]+)", p.get_text(strip=True).replace("\u00A0"," "))
        if m:
            data["PriceValue"] = int(m.group(1).replace(" ",""))

    # Parameters
    params = {}
    cont = soup.find("div", attrs={"data-testid": "ad-parameters-container"})
    if cont:
        for p in cont.find_all("p"):
            txt = p.get_text(strip=True)
            if ":" in txt:
                k,v = txt.split(":",1)
                params[k.strip()] = v.strip()
            else:
                params.setdefault("OtherInfo", []).append(txt)
    data["Parameters"] = params

    # Description
    dd = soup.find("div", attrs={"data-testid": "ad_description"})
    if dd and (inner:=dd.find("div")):
        data["Description"] = inner.get_text(" ", strip=True)

    # Images
    imgs=[]
    for c in soup.find_all("div", attrs={"data-testid":"ad-photo"}):
        if (img:=c.find("img")):
            src = img.get("src") or img.get("data-src")
            if src: imgs.append(urljoin(url,src))
    for img in soup.find_all("img",attrs={"data-testid":re.compile(r"swiper-image")}):
        src = img.get("src") or img.get("data-src")
        full = urljoin(url,src) if src else None
        if full and full not in imgs: imgs.append(full)
    data["Images"] = imgs

    # Location text
    loc=None
    for p in soup.find_all("p"):
        if p.get_text(strip=True)=="Местоположение":
            par=p.find_parent()
            if par:
                ps=[x.get_text(strip=True) for x in par.find_all("p") if x.get_text(strip=True)!="Местоположение"]
                loc=", ".join(ps)
            break
    if loc:
        # simplify to "X район" if contains "район"
        if "район" in loc:
            token=loc.split("район")[0].strip().split()[-2:]
            loc=" ".join(token)+" район"
        data["Location"]=loc

    # SellerName
    if (s:=soup.find(attrs={"data-testid":"user-profile-user-name"})):
        data["SellerName"]=s.get_text(strip=True)

    # MapLink & coords
    if (a:=soup.find("a", href=re.compile(r"maps\.google\.com/maps\?ll="))):
        href=a.get("href")
        ml=href if href.startswith("http") else urljoin(url,href)
        data["MapLink"]=ml
        # parse coords
        try:
            pq=parse_qs(urlparse(ml).query)
            ll= pq.get("ll") or pq.get("q")
            if ll:
                lat,lon=ll[0].split(",")[:2]
                data["Latitude"]=float(lat); data["Longitude"]=float(lon)
        except: pass

    # --- AI post‑processing ---
    # 1) redact phones
    data["Title"]       = redact_phone(data.get("Title",""))
    data["Description"] = redact_phone(data.get("Description",""))

    # 2) extract landmark if no map_link
    if not data.get("MapLink"):
        lm = extract_landmark(data["Title"]+" "+data["Description"])
        if lm:
            data["Landmark"] = lm

    # 3) translate into Russian
    full = f"{data['Title']}\n\n{data['Description']}"
    data["Description"] = translate(full, target_lang="Russian")

    return data
