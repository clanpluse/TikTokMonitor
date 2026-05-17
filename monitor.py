import os
import json
import requests
import feedparser
from anthropic import Anthropic
from datetime import datetime

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
RSSHUB_BASE = "https://rsshub.app/tiktok/user/@{}"

client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


def get_tiktok_feed(username):
    url = RSSHUB_BASE.format(username)
    feed = feedparser.parse(url)
    return feed.entries


def summarize_with_claude(title, description):
    if not client:
        return None
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": (
                f"لخص هذا الفيديو من تيك توك بالعربية في 3 نقاط رئيسية:\n"
                f"العنوان: {title}\n"
                f"الوصف: {description}\n\n"
                f"اكتب الملخص بشكل واضح ومختصر."
            )
        }]
    )
    return message.content[0].text


def load_seen_ids():
    try:
        with open('data/seen_ids.json', 'r') as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_seen_ids(ids):
    with open('data/seen_ids.json', 'w') as f:
        json.dump(list(ids), f)


def load_feed():
    try:
        with open('data/feed.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def save_feed(items):
    with open('data/feed.json', 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def load_accounts():
    try:
        with open('config/accounts.txt', 'r', encoding='utf-8') as f:
            return [
                line.strip()
                for line in f
                if line.strip() and not line.startswith('#')
            ]
    except Exception:
        return []


def main():
    accounts = load_accounts()
    if not accounts:
        print("No accounts to monitor.")
        return

    seen_ids = load_seen_ids()
    feed_items = load_feed()
    new_items = []

    for username in accounts:
        print(f"Checking @{username}...")
        try:
            entries = get_tiktok_feed(username)
            for entry in entries[:5]:
                video_id = entry.get('id') or entry.get('link', '')
                if video_id in seen_ids:
                    continue

                title = entry.get('title', '')
                description = entry.get('summary', '')

                item = {
                    'id': video_id,
                    'username': username,
                    'title': title,
                    'description': description,
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'timestamp': datetime.now().isoformat(),
                    'summary_ai': None
                }

                if client:
                    try:
                        item['summary_ai'] = summarize_with_claude(title, description)
                        print(f"  AI summary generated for: {title[:50]}")
                    except Exception as e:
                        print(f"  AI error: {e}")

                new_items.append(item)
                seen_ids.add(video_id)
                print(f"  New video: {title[:60]}")

        except Exception as e:
            print(f"Error for @{username}: {e}")

    if new_items:
        feed_items = new_items + feed_items
        feed_items = feed_items[:100]
        save_feed(feed_items)
        save_seen_ids(seen_ids)
        print(f"\nDone: {len(new_items)} new video(s) found.")
    else:
        print("\nNo new videos.")


if __name__ == '__main__':
    main()
