"""
Sends 1-2 random highlights to Telegram.
Reads config from environment variables (set as GitHub Actions secrets/vars):
  BOT_TOKEN        - Telegram bot token (secret)
  CHAT_ID          - Telegram chat id to send to (secret)
  CATEGORY_FILTER  - optional, comma-separated category names to restrict to.
                      Leave empty/unset to pick from all categories.
  NUM_HIGHLIGHTS   - optional, how many highlights to send (default 2)
"""

import json
import os
import random
import sys
import urllib.request
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "highlights.json")


def load_highlights():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def pick_highlights(highlights, category_filter, num):
    if category_filter:
        wanted = {c.strip() for c in category_filter.split(",") if c.strip()}
        pool = [h for h in highlights if h.get("category") in wanted]
    else:
        pool = highlights

    if not pool:
        print("No highlights matched the category filter:", category_filter)
        sys.exit(1)

    num = min(num, len(pool))
    return random.sample(pool, num)


def format_message(h):
    lines = [f"\U0001F4D6 <b>{escape(h['book'])}</b>"]
    meta_bits = []
    if h.get("section"):
        meta_bits.append(escape(h["section"]))
    if h.get("page"):
        meta_bits.append(f"p. {escape(h['page'])}")
    if meta_bits:
        lines.append(" · ".join(meta_bits))
    lines.append("")
    lines.append(f"\u201C{escape(h['text'])}\u201D")
    return "\n".join(lines)


def escape(text):
    # Minimal escaping for Telegram HTML parse mode
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def send_telegram_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }
    ).encode()

    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode()
        if resp.status != 200:
            print("Telegram API error:", body)
            sys.exit(1)
        return body


def main():
    bot_token = os.environ.get("BOT_TOKEN")
    chat_id = os.environ.get("CHAT_ID")
    if not bot_token or not chat_id:
        print("Missing BOT_TOKEN or CHAT_ID environment variables.")
        sys.exit(1)

    category_filter = os.environ.get("CATEGORY_FILTER", "").strip()
    num_highlights = int(os.environ.get("NUM_HIGHLIGHTS", "2"))

    highlights = load_highlights()
    chosen = pick_highlights(highlights, category_filter, num_highlights)

    for h in chosen:
        msg = format_message(h)
        send_telegram_message(bot_token, chat_id, msg)
        print("Sent highlight", h["id"], "-", h["book"])


if __name__ == "__main__":
    main()
