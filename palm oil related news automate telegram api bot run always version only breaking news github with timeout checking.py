# -*- coding: utf-8 -*-
"""
Created on Thu Sep 25 10:53:11 2025

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
#TO_ADDR         = "boonwui@uobkayhian.com"
#CC_ADDR         = "boonwui@uobkayhian.com"

#INCLUDE_KEYWORDS = ["palm oil", "soybean oil"]  # case-insensitive
EXCLUDE_KEYWORDS = ["eps", "dividend", "forecast", "technicals","www.buysellsignals.com", "Información de","Stock Exchange", "Exchange Group", "LTD","BERNAMA"]  # case-insensitive
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
        response = requests.post(url, json=payload, timeout=60)  # ⬅️ long Telegram timeout
        response.raise_for_status()
        print(f"✅ Sent to Telegram: {message[:50]}...")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send message: {e}")

# ---------------- LSEG safe wrapper ----------------
def safe_lseg_call(func, *args, retries=3, wait=10, **kwargs):
    """Retry wrapper for LSEG API calls (no timeout kw supported by SDK)"""
    for attempt in range(1, retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"⚠️ LSEG API call failed (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(wait)
            else:
                print("❌ All retries failed.")
                return None

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
    df_news = safe_lseg_call(
        ld.news.get_headlines,
        query="(Topic:POIL AND AA) OR (Topic:SOIL AND AA)",
        count=10
    )
    if df_news is None or df_news.empty:
        print("⚠️ No headlines fetched.")
        return

    if "language" in df_news.columns:
        df_news = df_news[df_news["language"].str.lower().isin(["en", "english"])]
    else:
        df_news = df_news[
            df_news["headline"].str.encode("ascii", "ignore").str.decode("ascii") == df_news["headline"]
        ]

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

        if version in last_versions:
            continue

        if headline.upper() != headline:
            continue

        # Step 4: Fetch story text with retry
        html = safe_lseg_call(ld.news.get_story, sid, format=ld.news.Format.HTML)
        if not html:
            html = safe_lseg_call(ld.news.get_story, sid, format=ld.news.Format.TEXT)
        if not html:
            continue

        text = BeautifulSoup(html, "html.parser").get_text()

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
        time.sleep(1800)
except KeyboardInterrupt:
    print("Script stopped by user.")
finally:
    session.close()