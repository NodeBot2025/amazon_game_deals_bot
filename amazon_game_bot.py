import requests
from bs4 import BeautifulSoup
import time
import os
import random
import re

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
POST_LIMIT = 3
USER_AGENT = {"User-Agent": "Mozilla/5.0"}

AMAZON_URL = "https://www.amazon.com/gp/goldbox"
FILTER_KEYWORDS = ["game", "xbox", "playstation", "nintendo", "switch", "controller", "console", "gaming", "ps5", "pc"]

def clean_title(text):
    text = re.sub(r"(?i)\b\d{1,3}%\s*off\b|\b\d{1,3}%\b|Limited time deal|Typical:|List:", "", text)
    text = re.sub(r"\$\d+(?:\.\d{2})?", "", text)
    return re.sub(r"\s+", " ", text).strip()

def generate_hashtags(title):
    words = re.findall(r"\b[A-Z][a-z]+|[a-z]{4,}\b", title)
    seen = set()
    tags = []
    for word in words:
        tag = "#" + re.sub(r"[^a-zA-Z0-9]", "", word.title())
        if tag not in seen and len(tag) > 4:
            tags.append(tag)
            seen.add(tag)
        if len(tags) >= 6:
            break
    return " ".join(tags)

def extract_price_data(block):
    prices = block.select(".a-offscreen")
    clean = [p.get_text(strip=True).replace("$", "") for p in prices if "$" in p.text]
    clean = list(dict.fromkeys(clean))
    if len(clean) >= 2:
        return clean[1], clean[0]
    elif clean:
        return clean[0], clean[0]
    return None, None

def get_image_url(block):
    img = block.select_one("img")
    return img["src"] if img else None

def post_to_facebook(caption, image_url):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
    payload = {
        "caption": caption,
        "url": image_url,
        "access_token": FB_ACCESS_TOKEN
    }
    res = requests.post(url, data=payload)
    print("[FB POST]", res.status_code, res.text)

def get_deals():
    print("[BOT STARTED]")
    print("[FILTER] Keywords:", FILTER_KEYWORDS)
    soup = BeautifulSoup(requests.get(AMAZON_URL, headers=USER_AGENT).text, "html.parser")
    blocks = soup.select("a[href*='/dp/']")
    print("[DEBUG] Found", len(blocks), "deal blocks.")
    random.shuffle(blocks)

    deals = []
    seen = set()

    for block in blocks:
        try:
            text = block.get_text(strip=True)
            title = clean_title(text)
            title_lower = title.lower()
            print("[DEBUG] Checking:", title_lower)

            if not any(kw in title_lower for kw in FILTER_KEYWORDS):
                continue

            href = block.get("href")
            if not title or not href or "/dp/" not in href:
                continue

            asin = href.split("/dp/")[1].split("/")[0].split("?")[0]
            if asin in seen:
                continue
            seen.add(asin)

            full_link = f"https://www.amazon.com/dp/{asin}?tag=amazongames04-20"
            parent = block.find_parent("div")

            list_price, deal_price = extract_price_data(parent or block)
            image_url = get_image_url(parent or block)

            if not (title and deal_price and image_url):
                continue

            hashtags = generate_hashtags(title)
            caption = f"🎮 {title}\nList: ${list_price} | Deal: ${deal_price}\n{full_link}\n\n{hashtags}"
            deals.append((caption, image_url))

            if len(deals) >= POST_LIMIT:
                break

        except Exception as e:
            print("[ERROR BLOCK]", e)

    return deals

def main():
    deals = get_deals()
    if not deals:
        print("[INFO] No deals found.")
        return
    for caption, image_url in deals:
        print("[POSTING DEAL]")
        post_to_facebook(caption, image_url)
        time.sleep(5)

if __name__ == "__main__":
    main()
