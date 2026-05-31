import os
import json
import subprocess
import requests
import base64
import tempfile
from anthropic import Anthropic
from datetime import datetime

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = "clanpluse/TikTokMonitor"

client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# Load Whisper model once at startup
whisper_model = None
def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        try:
            import whisper
            print("  Loading Whisper model...")
            whisper_model = whisper.load_model("tiny")
            print("  Whisper model loaded.")
        except Exception as e:
            print(f"  Whisper load error: {e}")
    return whisper_model


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


def download_audio(video_url):
    """Download audio from TikTok video and return path to audio file."""
    try:
        tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        tmp_path = tmp.name
        tmp.close()

        result = subprocess.run(
            [
                "yt-dlp",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "5",
                "--no-warnings",
                "--no-cache-dir",
                "-o", tmp_path,
                video_url
            ],
            capture_output=True,
            text=True,
            timeout=90
        )

        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            return tmp_path
        else:
            return None

    except Exception as e:
        print(f"  Audio download error: {e}")
        return None


def transcribe_audio(audio_path):
    """Transcribe audio file using Whisper. Returns text or None."""
    try:
        model = get_whisper_model()
        if not model:
            return None

        result = model.transcribe(audio_path, fp16=False)
        text = result.get("text", "").strip()
        return text if text else None

    except Exception as e:
        print(f"  Transcribe error: {e}")
        return None
    finally:
        try:
            if os.path.exists(audio_path):
                os.unlink(audio_path)
        except Exception:
            pass


def summarize_with_claude(title, description, transcript=None):
    if not client:
        return None
    try:
        if transcript:
            content = (
                f"لخص هذا الفيديو من تيك توك بالعربية في 3 نقاط رئيسية:\n"
                f"العنوان: {title}\n"
                f"النص المنطوق في الفيديو: {transcript}\n\n"
                f"اكتب الملخص بشكل واضح ومختصر."
            )
        else:
            content = (
                f"لخص هذا الفيديو من تيك توك بالعربية في 3 نقاط رئيسية:\n"
                f"العنوان: {title}\n"
                f"الوصف: {description}\n\n"
                f"اكتب الملخص بشكل واضح ومختصر."
            )

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": content}]
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

            # Download and transcribe audio
            transcript = None
            print(f"  Downloading audio for: {title[:40]}...")
            audio_path = download_audio(link)
            if audio_path:
                transcript = transcribe_audio(audio_path)
                if transcript:
                    print(f"  Transcript: {transcript[:60]}...")
                else:
                    print(f"  🔇 No speech detected")
            else:
                print(f"  Audio download failed, using metadata only")

            # Summarize with Claude
            if client and title:
                summary = summarize_with_claude(title, description, transcript)
                if transcript is None and audio_path is None:
                    # Could not download audio
                    item['summary_ai'] = summary
                elif transcript is None:
                    # Downloaded but no speech
                    item['summary_ai'] = "🔇 بدون صوت"
                else:
                    item['summary_ai'] = summary
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
