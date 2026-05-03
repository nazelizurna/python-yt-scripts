CHANNEL_IDS = [
    "UCCrEOOHDNC06tvzBkVRwwmQ", # Первый канал
    "UCdfeNL54iXtzejfTU1Yku6g",  # Второй канал

]

OUTPUT_DIR = "transcripts"
FILE_FORMAT = "txt"
OUTPUT_DIR  = "transcripts"
FILE_FORMAT = "txt"
FALLBACK_EN = False
SKIP_SHORTS = True

# 🔥 НОВЫЕ НАСТРОЙКИ
import random

DELAY_MIN = 3
DELAY_MAX = 7

BATCH_MIN = 8
BATCH_MAX = 15

SHORT_PAUSE = (20, 60)
LONG_PAUSE  = (120, 300)

RETRIES = 3

# ═══════════════════════════════════════════════════════════

import os, re, sys, time
from pathlib import Path
import requests

try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except ImportError:
    pass

try:
    import yt_dlp
except ImportError:
    sys.exit("❌ pip install yt-dlp")

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
    )
except ImportError:
    sys.exit("❌ pip install youtube-transcript-api")


# ─── Session (антибан) ─────────────────────────────────────

def make_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0"
    })
    return session


# ─── Форматирование ───────────────────────────────────────

def sanitize(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()[:120]


def fmt_srt_time(sec: float) -> str:
    ms = int((sec % 1) * 1000)
    s = int(sec)
    h, r = divmod(s, 3600)
    m, s = divmod(r, 60)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def to_txt(entries) -> str:
    if hasattr(entries, 'to_raw_data'):
        entries = entries.to_raw_data()
    return "\n".join(e["text"] for e in entries)


def to_srt(entries) -> str:
    if hasattr(entries, 'to_raw_data'):
        entries = entries.to_raw_data()
    out = []
    for i, e in enumerate(entries, 1):
        start = e["start"]
        end = start + e.get("duration", 2.0)
        out.append(f"{i}\n{fmt_srt_time(start)} --> {fmt_srt_time(end)}\n{e['text']}\n")
    return "\n".join(out)


# ─── Видео ────────────────────────────────────────────────

def get_videos(channel_id: str) -> list:
    url = f"https://www.youtube.com/channel/{channel_id}/videos"

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
        "nocheckcertificate": True,
        "cookiesfrombrowser": ("chrome",),  # 🔥 ДОБАВЛЕНО
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    entries = info.get("entries") or []

    flat = []
    for e in entries:
        if not e:
            continue
        if e.get("_type") == "playlist":
            flat.extend(sub for sub in (e.get("entries") or []) if sub)
        else:
            flat.append(e)

    return [
        {
            "id": e["id"],
            "title": e.get("title", e["id"]),
            "duration": e.get("duration") or 0,
        }
        for e in flat if e and e.get("id")
    ]


# ─── Транскрипт ───────────────────────────────────────────

def get_transcript(video_id: str):
    api = YouTubeTranscriptApi(http_client=make_session())  # 🔥 session

    transcript_list = api.list(video_id)

    langs_to_try = ["ru", "a.ru"]
    if FALLBACK_EN:
        langs_to_try += ["en", "a.en"]

    for lang in langs_to_try:
        try:
            transcript = transcript_list.find_transcript([lang])
            return transcript.fetch(), lang
        except NoTranscriptFound:
            continue

    raise RuntimeError("Транскрипт не найден")


# 🔥 RETRY LOGIC
def safe_get_transcript(video_id):
    for attempt in range(RETRIES):
        try:
            return get_transcript(video_id)
        except Exception as e:
            if attempt < RETRIES - 1:
                wait = (2 ** attempt) + random.uniform(1, 3)
                print(f"\n   ↻ retry через {wait:.1f} сек")
                time.sleep(wait)
            else:
                raise e


# ─── MAIN ─────────────────────────────────────────────────

# ─── MAIN ─────────────────────────────────────────────────

def main():
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    total_ok = total_already = total_failed = 0

    for channel_id in CHANNEL_IDS:                     # ←←← Главное изменение
        print(f"\n{'='*80}")
        print(f"📺 Обрабатываем канал: {channel_id}")
        print(f"{'='*80}\n")

        try:
            videos = get_videos(channel_id)

            if SKIP_SHORTS:
                videos = [v for v in videos if v["duration"] >= 60]

            random.shuffle(videos)

            batch_limit = random.randint(BATCH_MIN, BATCH_MAX)
            batch_count = 0

            ok = already = failed = 0

            for i, video in enumerate(videos, 1):
                vid_id = video["id"]
                title = sanitize(video["title"])
                filepath = out_dir / f"{title}_[{vid_id}].{FILE_FORMAT}"

                print(f"[{i}/{len(videos)}] {video['title'][:60]}... ", end="")

                if filepath.exists():
                    print("уже есть")
                    already += 1
                    continue

                try:
                    fetched, lang = safe_get_transcript(vid_id)

                    text = to_srt(fetched) if FILE_FORMAT == "srt" else to_txt(fetched)
                    filepath.write_text(text, encoding="utf-8")

                    print(f"✓ [{lang}]")
                    ok += 1
                    batch_count += 1

                except Exception as e:
                    print(f"✗ {e}")
                    failed += 1

                # Задержки
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

                if batch_count >= batch_limit:
                    pause = random.uniform(*SHORT_PAUSE)
                    print(f"\n⏸ Пауза {pause:.0f} сек\n")
                    time.sleep(pause)

                    if random.random() < 0.3:
                        long_pause = random.uniform(*LONG_PAUSE)
                        print(f"🛑 Длинная пауза {long_pause:.0f} сек\n")
                        time.sleep(long_pause)

                    batch_limit = random.randint(BATCH_MIN, BATCH_MAX)
                    batch_count = 0

            print(f"\n✅ Канал завершён: OK: {ok} | Уже было: {already} | Ошибок: {failed}")

            total_ok += ok
            total_already += already
            total_failed += failed

        except Exception as e:
            print(f"❌ Ошибка при обработке канала {channel_id}: {e}")

    print("\n" + "="*80)
    print("ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
    print(f"Всего OK: {total_ok}")
    print(f"Всего уже было: {total_already}")
    print(f"Всего ошибок: {total_failed}")
    print("="*80)
if __name__ == "__main__":
    main()
