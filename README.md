# physical-palm-oil-news-emailer (1st File)
Automated Python script to fetch physical palm oil price news from LSEG, filter relevant headlines, and send daily update emails via Outlook.

Repository Description Examples

Automated email alerts for Malaysian, Indonesian, and European physical palm oil price news using LSEG Data API and Outlook.

Python script to fetch and filter palm oil price news headlines, then send update emails via Outlook.

Automatically monitors palm oil price stories from LSEG and sends daily email reports with new updates.

Email notification system for physical palm oil price news leveraging LSEG API and Outlook automation.

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Palm & Soybean Oil News Auto-Notifier (2nd File)

This project automates the process of fetching and filtering news from Reuters via the LSEG Data API, with results automatically delivered to a Telegram group or channel.

🔎 Features

Automated News Fetching: Queries Reuters for the latest Palm Oil and Soybean Oil news.

Breaking News Filter: Keeps only stories tagged as Breaking News.

Headline Filtering: Sends only headlines written in ALL CAPS for stronger relevance (e.g., official breaking headlines).

Language Control: Keeps only English-language stories.

Keyword Exclusions: Skips irrelevant stories containing words like EPS, dividend, forecast, technicals, etc.

Duplicate Control: Uses local state tracking to avoid resending the same news.

Telegram Integration: Pushes clean and formatted stories directly to a Telegram chat via bot API.

⚙️ How It Works

Script queries Reuters (palm oil and soybean oil).

Filters results through multiple layers:

Breaking News only

English only

All-caps headlines only

Exclusion keyword check

New and valid stories are formatted and sent to the configured Telegram chat.

Runs continuously, polling every 30 minutes (default).

📦 Requirements

Python 3.9+

lseg.data, beautifulsoup4, rapidfuzz, requests, pywin32

Install dependencies:

pip install lseg.data beautifulsoup4 rapidfuzz requests pywin32

🚀 Usage

Configure your LSEG API key and workspace.

Set your Telegram Bot Token and Chat ID in the script.

Run the script
