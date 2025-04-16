import requests
import hashlib
import hmac
import base64
import datetime
import json
import os
import time

# === CREDENTIALS ===
ACCESS_KEY = "AKPARFMRQS1744843266"
SECRET_KEY = "3VqJat+OOZXddc2iL00w6+LR5slKvDXIEg6EOFqJ"
ASSOCIATE_TAG = "amazongames04-20"
REGION = "us-east-1"
HOST = "webservices.amazon.com"
ENDPOINT = f"https://{HOST}/paapi5/searchitems"

# === FACEBOOK PAGE ===
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

# === HEADERS ===
SERVICE = "ProductAdvertisingAPI"
CONTENT_TYPE = "application/json; charset=utf-8"

def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def get_signature_key(key, date_stamp, regionName, serviceName):
    kDate = sign(("AWS4" + key).encode("utf-8"), date_stamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, "aws4_request")
    return kSigning

def build_paapi_request():
    payload = {
        "Keywords": "video game",
        "SearchIndex": "VideoGames",
        "ItemCount": 3,
        "Resources": [
            "Images.Primary.Medium",
            "ItemInfo.Title",
            "Offers.Listings.Price",
            "Offers.Listings.SavingBasis"
        ],
        "PartnerTag": ASSOCIATE_TAG,
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.com"
    }

    amz_date = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    date_stamp = datetime.datetime.utcnow().strftime("%Y%m%d")

    canonical_uri = "/paapi5/searchitems"
    canonical_querystring = ""
    payload_json = json.dumps(payload)

    canonical_headers = f"content-encoding:amz-1.0\ncontent-type:{CONTENT_TYPE}\nhost:{HOST}\nx-amz-date:{amz_date}\n"
    signed_headers = "content-encoding;content-type;host;x-amz-date"
    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

    canonical_request = f"POST\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{REGION}/{SERVICE}/aws4_request"
    string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

    signing_key = get_signature_key(SECRET_KEY, date_stamp, REGION, SERVICE)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    headers = {
        "Content-Encoding": "amz-1.0",
        "Content-Type": CONTENT_TYPE,
        "Host": HOST,
        "X-Amz-Date": amz_date,
        "X-Amz-Target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
        "Authorization": f"{algorithm} Credential={ACCESS_KEY}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    }

    return headers, payload_json

def post_to_facebook(caption, image_url):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
    payload = {
        "caption": caption,
        "url": image_url,
        "access_token": FB_ACCESS_TOKEN
    }
    res = requests.post(url, data=payload)
    print("[FB POST]", res.status_code, res.text)

def main():
    headers, body = build_paapi_request()
    response = requests.post(ENDPOINT, headers=headers, data=body)
    data = response.json()

    if "SearchResult" not in data or "Items" not in data["SearchResult"]:
        print("[INFO] No items returned from Amazon API.")
        print(data)
        return

    for item in data["SearchResult"]["Items"]:
        title = item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue", "")
        url = item.get("DetailPageURL", "")
        image = item.get("Images", {}).get("Primary", {}).get("Medium", {}).get("URL", "")
        offers = item.get("Offers", {}).get("Listings", [{}])[0]
        price = offers.get("Price", {}).get("DisplayAmount", "")
        saving = offers.get("SavingBasis", {}).get("DisplayAmount", "")

        caption = f"🎮 {title}\nPrice: {price}\n{url}\n#Amazon #GameDeals"
        post_to_facebook(caption, image)
        time.sleep(5)

if __name__ == "__main__":
    main()
