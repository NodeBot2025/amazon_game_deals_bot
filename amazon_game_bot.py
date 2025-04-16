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

AMAZON_URL = "https://www.amazon.com/Video-Games-Deals"

CONSOLE_KEYWORDS = ["xbox", "playstation", "ps5", "nintendo", "switch", "controller", "game", "video", "console", "gaming", "pc"]
CONSOLE_FILTER = random.sample(CONSOLE_KEYWORDS, k=3)

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
    prices = block.select(".a-price-whole")
    clean = [p.get_text(strip=True) for p in prices if p.get_text(strip=True).isdigit()]
    if len(clean) >= 1:
        return clean[0]
    return None

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
    print("[FILTER] Using keywords:", CONSOLE_FILTER)
    soup = BeautifulSoup(requests.get(AMAZON_URL, headers=USER_AGENT).text, "html.parser")
    blocks = soup.select("div[data-asin][data-component-type='s-search-result']")
    random.shuffle(blocks)

    deals = []
    fallback_titles = []
    seen = set()

    for block in blocks:
        try:
            title_tag = block.select_one("h2 a span")
            href_tag = block.select_one("h2 a")
            if not title_tag or not href_tag:
                continue
            title = clean_title(title_tag.text.strip())
            href = "https://www.amazon.com" + href_tag.get("href")
            title_text = title.lower()

            if title in seen:
                continue
            seen.add(title)

            if not any(kw in title_text for kw in CONSOLE_FILTER):
                fallback_titles.append(block)
                continue

            price = extract_price_data(block)
            image_url = get_image_url(block)
            if not (title and price and image_url):
                continue

            hashtags = generate_hashtags(title)
            caption = f"🎮 {title}\nPrice: ${price}\n{href}\n\n{hashtags}"
            deals.append((caption, image_url))
            if len(deals) >= POST_LIMIT:
                break

        except Exception as e:
            print("[ERROR BLOCK]", e)

    if not deals and fallback_titles:
        print("[FALLBACK] No match found — using general titles.")
        for block in fallback_titles[:POST_LIMIT]:
            try:
                title_tag = block.select_one("h2 a span")
                href_tag = block.select_one("h2 a")
                if not title_tag or not href_tag:
                    continue
                title = clean_title(title_tag.text.strip())
                href = "https://www.amazon.com" + href_tag.get("href")
                price = extract_price_data(block)
                image_url = get_image_url(block)
                if not (title and price and image_url):
                    continue
                hashtags = generate_hashtags(title)
                caption = f"🎮 {title}\nPrice: ${price}\n{href}\n\n{hashtags}"
                deals.append((caption, image_url))
            except Exception as e:
                print("[FALLBACK ERROR]", e)

    return deals

def main():
    print("[BOT STARTED]")
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
