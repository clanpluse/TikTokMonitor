import os
import json
import subprocess
import requests
import base64
from anthropic import Anthropic
from datetime import datetime

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = "clanpluse/TikTokMonitor"

client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


def get_tiktok_videos(username):
    """Get latest videos from TikTok using yt-dlp."""
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--flat-playlist",
                "--dump-json",
                "--playlist-end", "10",
                "--no-warnings",
                "--no-cache-dir",
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


def github_get_file(path):
    """Get file content and SHA from GitHub."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        content = base64.b64decode(data['content']).decode('utf-8')
        return content, data['sha']
    return None, None


def github_update_file(path, content, sha, message):
    """Update file content on GitHub."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    body = {
        "message": message,
        "content": encoded,
        "sha": sha
    }
    response = requests.put(url, headers=headers, json=body)
    return response.status_code in [200, 201]


def load_seen_ids():
    content, _ = github_get_file('data/seen_ids.json')
    if content:
        try:
            return set(json.loads(content))
        except Exception:
            pass
    return set()


def save_seen_ids(ids):
    content, sha = github_get_file('data/seen_ids.json')
    new_content = json.dumps(list(ids))
    if sha:
        github_update_file('data/seen_ids.json', new_content, sha, "Update seen IDs")
    print("  Saved seen IDs")


def load_feed():
    content, _ = github_get_file('data/feed.json')
    if content:
        try:
            return json.loads(content)
        except Exception:
            pass
    return []


def save_feed(items):
    content, sha = github_get_file('data/feed.json')
    new_content = json.dumps(items, ensure_ascii=False, indent=2)
    if sha:
        success = github_update_file('data/feed.json', new_content, sha, "Update feed")
        print(f"  Feed saved: {success}")


def load_accounts():
    content, _ = github_get_file('config/accounts.txt')
    if content:
        return [
            line.strip()
            for line in content.split('\n')
            if line.strip() and not line.startswith('#')
        ]
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
