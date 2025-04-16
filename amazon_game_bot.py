import requests 
from bs4 import BeautifulSoup
import time
import os
import random
import re
from dotenv import load_dotenv

load_dotenv()

AMAZON_URL = "https://www.amazon.com/s?i=videogames&rh=n%3A468642"
AFFILIATE_TAG = "?tag=amazongames04-20"
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
POST_LIMIT = 5
USER_AGENT = {"User-Agent": "Mozilla/5.0"}

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

def calculate_discount(list_price, deal_price):
    try:
        return f"{round((float(list_price) - float(deal_price)) / float(list_price) * 100)}% off"
    except:
        return None

def clean_title(text):
    text = re.sub(r'(?i)\b\d{1,3}%\s*off\b|\b\d{1,3}%\b|Limited time deal|Typical:|List:', '', text)
    text = re.sub(r'\$\d+(?:\.\d{2})?', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def generate_hashtags(title):
    words = re.findall(r"\b[A-Z][a-z]+|[a-z]{4,}\b", title)
    seen = set()
    tags = []
    for word in words:
        tag = "#" + re.sub(r'[^a-zA-Z0-9]', '', word.title())
        if tag not in seen and len(tag) > 4:
            tags.append(tag)
            seen.add(tag)
        if len(tags) >= 6:
            break
    return " ".join(tags)

def post_to_facebook(caption, image_url):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
    payload = {
        "caption": caption,
        "url": image_url,
        "access_token": FB_ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    print("[FB POST]", response.status_code, response.text)

def get_deals():
    soup = BeautifulSoup(requests.get(AMAZON_URL, headers=USER_AGENT).text, "html.parser")
    blocks = soup.select("a[href*='/dp/']")
    random.shuffle(blocks)

    deals = []
    seen = set()

    for block in blocks:
        try:
            text = block.get_text(strip=True)
            title = clean_title(text)
            href = block.get("href")
            if not title or not href or "/dp/" not in href:
                continue

            if not any(kw in title.lower() for kw in ["game", "xbox", "playstation", "ps5", "nintendo", "switch", "controller"]):
                continue

            asin = href.split("/dp/")[1].split("/")[0].split("?")[0]
            if asin in seen:
                continue
            seen.add(asin)

            full_link = f"https://www.amazon.com/dp/{asin}{AFFILIATE_TAG}"
            parent = block.find_parent("div")

            list_price, deal_price = extract_price_data(parent or block)
            image_url = get_image_url(parent or block)
            discount = calculate_discount(list_price, deal_price)

            if not (title and discount and list_price and deal_price and image_url):
                continue

            hashtags = generate_hashtags(title)
            caption = f"{discount}  {title}\n{discount} - List: ${list_price} | Deal: ${deal_price}\nLink: {full_link}\n\n{hashtags}"
            deals.append((caption, image_url))
            if len(deals) >= POST_LIMIT:
                break

        except Exception as e:
            print("[ERROR BLOCK]", e)

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
        time.sleep(10)

if __name__ == "__main__":
    main()
