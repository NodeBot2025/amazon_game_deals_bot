# Amazon Game Deals Auto Poster

Automatically scrapes Amazon video game deals and posts them to Facebook with your affiliate link every 6 hours.

## Features
- Auto scrape Amazon game category
- Post to Facebook Page with caption, image, and hashtags
- Includes affiliate tracking link

## Setup

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/YOUR_USERNAME/amazon_game_deals_bot.git
cd amazon_game_deals_bot
pip install -r requirements.txt
```

### 2. Configure Facebook API
- Create a Meta Developer App
- Get a Page Access Token with `pages_manage_posts` permission
- Replace `FB_PAGE_ID` and `FB_ACCESS_TOKEN` in `amazon_game_bot.py`

### 3. Test the Bot
```bash
python amazon_game_bot.py
```

### 4. Schedule Every 6 Hours

#### On Linux (Cron):
```bash
crontab -e
```
Add this line:
```cron
0 */6 * * * /usr/bin/python3 /path/to/amazon_game_bot.py >> /path/to/log.txt 2>&1
```

#### On Windows (Task Scheduler):
- Create task
- Set trigger: Repeat every 6 hours
- Action: Start a program → `python`
- Arguments: `C:\path\to\amazon_game_bot.py`

---

### Notes
- Be sure to test the Facebook token manually before automating.
- Use shortened affiliate links for cleaner posts (optional).
