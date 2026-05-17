import os
import json
import subprocess
from anthropic import Anthropic
from datetime import datetime

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


def get_tiktok_videos(username):
    """Get latest videos from TikTok using yt-dlp."""
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--flat-playlist",
                "--dump-json",
                "--playlist-end", "5",
                "--no-warnings",
                f"https://www.tiktok.com/@{username}"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        videos = []
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if line:
                try:
                    videos.append(json.loads(line))
                except Exception:
                    pass

        print(f"  yt-dlp found {len(videos)} videos")
        return videos

    except subprocess.TimeoutExpired:
        print(f"  Timeout for @{username}")
        return []
    except Exception as e:
        print(f"  Error: {e}")
        return []


def summarize_with_claude(title, description):
    if not client:
        return None
    try:
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
    except Exception as e:
        print(f"  Claude error: {e}")
        return None


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

    print(f"Monitoring {len(accounts)} accounts: {accounts}")

    seen_ids = load_seen_ids()
    feed_items = load_feed()
    new_items = []

    for username in accounts:
        print(f"\nChecking @{username}...")
        videos = get_tiktok_videos(username)

        for video in videos:
            video_id = str(video.get('id', video.get('webpage_url', '')))
            if video_id in seen_ids:
                continue

            title = video.get('title', '') or video.get('description', '')
            description = video.get('description', '') or title
            link = video.get('webpage_url', f"https://www.tiktok.com/@{username}")

            item = {
                'id': video_id,
                'username': username,
                'title': title,
                'description': description,
                'link': link,
                'published': video.get('upload_date', datetime.now().strftime('%Y%m%d')),
                'timestamp': datetime.now().isoformat(),
                'summary_ai': None
            }

            if client and title:
                item['summary_ai'] = summarize_with_claude(title, description)
                print(f"  AI summary: done")

            new_items.append(item)
            seen_ids.add(video_id)
            print(f"  New video: {title[:60]}")

    if new_items:
        feed_items = new_items + feed_items
        feed_items = feed_items[:100]
        save_feed(feed_items)
        save_seen_ids(seen_ids)
        print(f"\nDone: {len(new_items)} new video(s) saved.")
    else:
        print("\nNo new videos found.")


if __name__ == '__main__':
    main()
