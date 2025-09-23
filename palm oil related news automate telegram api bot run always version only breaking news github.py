# -*- coding: utf-8 -*-
"""
Created on Tue Sep 23 13:54:28 2025

@author: BWLAU
"""


# -*- coding: utf-8 -*-
"""
Created on Mon Sep 22 15:11:11 2025

@author: BWLAU
"""
import os
import json
import pythoncom
import win32com.client
import lseg.data as ld       # pip install lseg.data
from datetime import date, datetime
from bs4 import BeautifulSoup  # pip install beautifulsoup4
from rapidfuzz import fuzz
import requests
import time

# --- Configuration -----------------------------------------------------------
STATE_FILE      = "sent_palm_news_state_10.json"
LSEG_APP_KEY    = ""
WORKSPACE_NAME  = "workspace"
#TO_ADDR         = ""
#CC_ADDR         = ""

#INCLUDE_KEYWORDS = ["palm oil", "soybean oil"]  # case-insensitive
EXCLUDE_KEYWORDS = ["eps", "dividend", "forecast", "technicals","www.buysellsignals.com", "Información de","Stock Exchange", "Exchange Group", "LTD"]  # case-insensitive
# ----------------------------------------

# Telegram Bot Configuration
BOT_TOKEN = ""
CHAT_ID = -

# ---------------- State Load/Save ----------------
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ---------------- Telegram send function ----------------
def send_telegram_message(chat_id, message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        print(f"✅ Sent to Telegram: {message[:50]}...")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send message: {e}")

# ---------------- Initialize LSEG Session ----------------
session = ld.session.desktop.Definition(
    name=WORKSPACE_NAME,
    app_key=LSEG_APP_KEY
).get_session()
session.open()
ld.session.set_default(session)

# ---------------- Main function ----------------
def fetch_and_send_news():
    # Step 1: Get Reuters headlines (Palm oil OR Soybean oil search)
    df_news = ld.news.get_headlines(
        query="palm oil OR soybean oil",
        count=20
    )

    if "language" in df_news.columns:
        df_news = df_news[df_news["language"].str.lower().isin(["en", "english"])]
    else:
        # fallback: try to filter by headline charset
        df_news = df_news[df_news["headline"].str.encode("ascii", "ignore").str.decode("ascii") == df_news["headline"]]

    # Step 2: Keep only Breaking News
    if "category" in df_news.columns:
        df_news = df_news[df_news["category"].str.lower() == "breaking news"]

    state = load_state()
    last_versions = state.get("versions", [])
    new_versions = last_versions.copy()
    new_news_found = False

    for idx, sid in df_news["storyId"].items():
        headline = str(df_news.at[idx, "headline"]).strip()
        version  = str(idx)

        # Skip if already processed
        if version in last_versions:
            continue

        # Step 3: Must be ALL CAPS
        if headline.upper() != headline:
            continue

        # Step 4: Fetch story text
        html = ld.news.get_story(sid, format=ld.news.Format.HTML)
        if not html:
            html = ld.news.get_story(sid, format=ld.news.Format.TEXT)
        if not html:
            continue

        text = BeautifulSoup(html, "html.parser").get_text()

        # Step 5: Exclude unwanted keywords
        if any(kw.lower() in headline.lower() or kw.lower() in text.lower()
               for kw in EXCLUDE_KEYWORDS if kw):
            continue

        # ✅ Passed all filters → Send to Telegram
        message = f"<b>{headline}</b>\n\n{text}"
        send_telegram_message(CHAT_ID, message)

        new_versions.append(version)
        new_news_found = True

    if new_news_found:
        state["versions"] = new_versions
        save_state(state)

# ---------------- Continuous loop every 30 mins ----------------
try:
    while True:
        print("⏱ Checking for Breaking News on Palm Oil & Soybean Oil...")
        fetch_and_send_news()
        print("Sleeping for 30 minutes...\n")
        time.sleep(1800)  # 30 minutes
except KeyboardInterrupt:
    print("Script stopped by user.")
finally:
    session.close()