"""
Sends 1-2 random highlights to Telegram, pulled live from Supabase.

Reads config from environment variables (set as GitHub Actions secrets/vars):
  BOT_TOKEN               - Telegram bot token (secret)
  CHAT_ID                 - Telegram chat id to send to (secret)
  SUPABASE_URL            - your project URL (secret or var, either is fine)
  SUPABASE_ANON_KEY       - the anon/public key (safe to store as a var; it can
                             only read, thanks to Row Level Security)
  CATEGORY_FILTER         - optional, restrict to one category
  NUM_HIGHLIGHTS          - optional, how many highlights to send (default 2)
"""

import os
import sys
import urllib.request
import urllib.parse
import json

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
CATEGORY_FILTER = os.environ.get("CATEGORY_FILTER", "").strip() or None
NUM_HIGHLIGHTS = int(os.environ.get("NUM_HIGHLIGHTS", "2"))


def fetch_random_highlights(n, category=None):
    url = f"{SUPABASE_URL}/rest/v1/rpc/random_highlights"
    payload = json.dumps({"n": n, "category_filter": category}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def escape(text):
    for ch in ("&", "<", ">"):
        text = text.replace(ch, {"&": "&amp;", "<": "&lt;", ">": "&gt;"}[ch])
    return text


def format_message(h):
    lines = [f"\U0001F4D6 <b>{escape(h['book_title'])}</b>"]
    meta_bits = []
    if h.get("section"):
        meta_bits.append(escape(h["section"]))
    if h.get("page"):
        meta_bits.append(f"p. {escape(str(h['page']))}")
    if meta_bits:
        lines.append(" · ".join(meta_bits))
    lines.append("")
    lines.append(escape(h["text"]))
    return "\n".join(lines)


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def main():
    highlights = fetch_random_highlights(NUM_HIGHLIGHTS, CATEGORY_FILTER)
    if not highlights:
        print("No highlights returned from Supabase.")
        sys.exit(1)

    for h in highlights:
        send_telegram(format_message(h))
        print(f"Sent: {h['book_title']}")


if __name__ == "__main__":
    main()
