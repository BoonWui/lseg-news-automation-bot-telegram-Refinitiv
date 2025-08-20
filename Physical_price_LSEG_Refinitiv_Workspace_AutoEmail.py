# -*- coding: utf-8 -*-
"""
Created on Wed Aug 20 17:41:26 2025

@author: BWLAU
"""


#!/usr/bin/env python3
import os
import json
import pythoncom
import win32com.client
import lseg.data as ld       # pip install lseg.data
from datetime import date, datetime
from bs4 import BeautifulSoup  # pip install beautifulsoup4

# --- Configuration -----------------------------------------------------------
STATE_FILE      = "sent_state.json"
LSEG_APP_KEY    = "YOUR_LSEG_APP_KEY"  # <-- REDACTED
WORKSPACE_NAME  = "workspace"
TO_ADDR         = "your_email@example.com"       # <-- REDACTED
CC_ADDR         = "your_cc_email@example.com"    # <-- REDACTED

# --- State Load/Save ----------------------------------------------------------
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# --- Filter Logic -------------------------------------------------------------
def is_physical_price_story(text: str) -> bool:
    must_have = [
        "MALAYSIAN CRUDE PALM OIL",
        "RBD PALM OLEIN",
        "INDONESIAN CPO",
        "BID", "ASK",
    ]
    t = text.upper()
    return all(kw in t for kw in must_have)

# --- Initialize LSEG Session --------------------------------------------------
session = ld.session.desktop.Definition(
    name=WORKSPACE_NAME,
    app_key=LSEG_APP_KEY
).get_session()
session.open()
ld.session.set_default(session)

# --- Initialize COM for Outlook -----------------------------------------------
pythoncom.CoInitialize()

# --- Fetch Headlines ----------------------------------------------------------
df_MY   = ld.news.get_headlines("Malaysian physical palm oil prices", count=3)
df_Indo = ld.news.get_headlines("Indonesia physical palm oil prices", count=1)
df_EU   = ld.news.get_headlines("European vegetable oil prices 1600 GMT", count=1)

# --- Select + Filter MY Story -------------------------------------------------
selected_my_story    = None
selected_my_headline = None
selected_my_version  = None

for idx, sid in df_MY["storyId"].items():
    html = ld.news.get_story(sid, format=ld.news.Format.HTML)
    text = BeautifulSoup(html, "html.parser").get_text()
    if is_physical_price_story(text):
        selected_my_story    = html
        selected_my_headline = df_MY.at[idx, "headline"]
        selected_my_version  = str(idx)
        break

# Fallback: use the first story if none matched
if not selected_my_story:
    idx0                 = df_MY.index[0]
    selected_my_story    = ld.news.get_story(df_MY.storyId.iloc[0], format=ld.news.Format.HTML)
    selected_my_headline = df_MY.headline.iloc[0]
    selected_my_version  = str(idx0)

# --- Select INDO and EU Stories ------------------------------------------------
indo_idx               = df_Indo.index[0]
selected_indo_story    = ld.news.get_story(df_Indo.storyId.iloc[0], format=ld.news.Format.HTML)
selected_indo_headline = df_Indo.headline.iloc[0]
selected_indo_version  = str(indo_idx)

eu_idx                = df_EU.index[0]
selected_eu_story     = ld.news.get_story(df_EU.storyId.iloc[0], format=ld.news.Format.HTML)
selected_eu_headline  = df_EU.headline.iloc[0]
selected_eu_version   = str(eu_idx)

# --- Load last sent versions --------------------------------------------------
state = load_state()
last_my_version   = state.get("my_version")
last_indo_version = state.get("indo_version")
last_eu_version   = state.get("eu_version")

# --- Check for new stories ----------------------------------------------------
current_my_dt   = datetime.fromisoformat(selected_my_version)
current_indo_dt = datetime.fromisoformat(selected_indo_version)
current_eu_dt   = datetime.fromisoformat(selected_eu_version)

should_send_my   = (not last_my_version) or (current_my_dt > datetime.fromisoformat(last_my_version))
should_send_indo = (not last_indo_version) or (current_indo_dt > datetime.fromisoformat(last_indo_version))
should_send_eu   = (not last_eu_version)   or (current_eu_dt   > datetime.fromisoformat(last_eu_version))

# --- Connect to Outlook -------------------------------------------------------
try:
    outlook = win32com.client.GetActiveObject("Outlook.Application")
except Exception:
    outlook = win32com.client.DispatchEx("Outlook.Application")

def send_email_html(to, cc, subject, html_body):
    mail = outlook.CreateItem(0)  # olMailItem
    mail.To       = to
    mail.CC       = cc
    mail.Subject  = subject
    mail.HTMLBody = html_body
    mail.Send()

# --- Send Emails if New -------------------------------------------------------
today = date.today().strftime("%Y-%m-%d")

if should_send_my:
    body = (
        f"<p>Hi Team,</p>\n"
        f"{selected_my_story}\n"
        f"<p>Regards,<br/>Your Team</p>"
    )
    send_email_html(TO_ADDR, CC_ADDR, selected_my_headline, body)
    print("MY story email sent!")
    state["my_version"] = selected_my_version
else:
    print("No new MY story; skipping.")

if should_send_indo:
    body = (
        f"<p>Hi Team,</p>\n"
        f"{selected_indo_story}\n"
        f"<p>Regards,<br/>Your Team</p>"
    )
    send_email_html(TO_ADDR, CC_ADDR, selected_indo_headline, body)
    print("Indo story email sent!")
    state["indo_version"] = selected_indo_version
else:
    print("No new Indo story; skipping.")

if should_send_eu:
    body = (
        f"<p>Hi Team,</p>\n"
        f"{selected_eu_story}\n"
        f"<p>Regards,<br/>Your Team</p>"
    )
    send_email_html(TO_ADDR, CC_ADDR, selected_eu_headline, body)
    print("EU story email sent!")
    state["eu_version"] = selected_eu_version
else:
    print("No new EU story; skipping.")

# --- Save State and Close Session ---------------------------------------------
save_state(state)
session.close()
