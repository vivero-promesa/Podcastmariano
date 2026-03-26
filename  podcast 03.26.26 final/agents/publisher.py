import os
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

PODCAST_CONFIG = {
    "title":       "Cápsulas Marianas",
    "description": "Episodios breves sobre misterios, advocaciones y espiritualidad mariana.",
    "author":      "Podcast Mariano AI",
    "email":       "tu-email@ejemplo.com",
    "website":     "https://vivero-promesa.github.io/Podcastelena",
    "image_url":   "https://vivero-promesa.github.io/Podcastelena/cover.jpg",
    "language":    "es",
    "category":    "Religion &amp; Spirituality",
    "explicit":    "false",
}

EPISODES_DB   = Path("data/episodes.json")
RSS_OUTPUT    = Path("docs/feed.xml")
AUDIO_WEBROOT = "{website}/audio"


def _load_episodes() -> list:
    if EPISODES_DB.exists():
        with open(EPISODES_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_episodes(episodes: list):
    EPISODES_DB.parent.mkdir(parents=True, exist_ok=True)
    with open(EPISODES_DB, "w", encoding="utf-8") as f:
        json.dump(episodes, f, ensure_ascii=False, indent=2)


def _rfc2822_now() -> str:
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")


def _file_size_bytes(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def _episode_to_item(ep: dict, cfg: dict) -> str:
    audio_url = AUDIO_WEBROOT.format(website=cfg["website"]) + "/" + ep["filename"]
    return f"""
    <item>
      <title>{ep['title']}</title>
      <description><![CDATA[{ep['description']}]]></description>
      <pubDate>{ep['pub_date']}</pubDate>
      <guid isPermaLink="false">{ep['guid']}</guid>
      <enclosure url="{audio_url}" length="{ep['size_bytes']}" type="audio/mpeg"/>
      <itunes:title>{ep['title']}</itunes:title>
      <itunes:summary><![CDATA[{ep['description']}]]></itunes:summary>
      <itunes:duration>{ep.get('duration', '00:02:30')}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
      <itunes:episode>{ep['episode_number']}</itunes:episode>
    </item>"""


def _build_rss(episodes: list, cfg: dict) -> str:
    items = "\n".join(_episode_to_item(ep, cfg) for ep in reversed(episodes))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
  xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{cfg['title']}</title>
    <link>{cfg['website']}</link>
    <description>{cfg['description']}</description>
    <language>{cfg['language']}</language>
    <itunes:author>{cfg['author']}</itunes:author>
    <itunes:email>{cfg['email']}</itunes:email>
    <itunes:image href="{cfg['image_url']}"/>
    <itunes:category text="{cfg['category']}"/>
    <itunes:explicit>{cfg['explicit']}</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    {items}
  </channel>
</rss>"""


def publisher_agent(state: dict) -> dict:
    print("📡 [Publisher] Registrando episodio y actualizando RSS...")

    audio_path = state.get("audio_path", "")
    topic      = state.get("topic", "Episodio sin título")
    script     = state.get("script", "")

    if not audio_path or not Path(audio_path).exists():
        msg = f"❌ Audio no encontrado: {audio_path}"
        print(msg)
        return {**state, "publish_error": msg}

    episodes       = _load_episodes()
    episode_number = len(episodes) + 1
    filename       = Path(audio_path).name

    audio_dest = Path("docs/audio")
    audio_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(audio_path, audio_dest / filename)
    print(f"  ✓ Audio → docs/audio/{filename}")

    episode = {
        "episode_number": episode_number,
        "guid":           f"capsulas-marianas-ep-{episode_number:03d}",
        "title":          f"Ep. {episode_number:03d} — {topic}",
        "description":    _extract_description(script),
        "filename":       filename,
        "audio_path":     str(audio_dest / filename),
        "size_bytes":     _file_size_bytes(str(audio_dest / filename)),
        "duration":       "00:02:30",
        "pub_date":       _rfc2822_now(),
        "topic":          topic,
    }

    episodes.append(episode)
    _save_episodes(episodes)
    print(f"  ✓ Episodio #{episode_number} guardado")

    RSS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    RSS_OUTPUT.write_text(_build_rss(episodes, PODCAST_CONFIG), encoding="utf-8")
    print(f"  ✓ RSS actualizado → {RSS_OUTPUT}")
    print(f"\n✅ Haz git push para publicar en Spotify.")
    print(f"   RSS: {PODCAST_CONFIG['website']}/feed.xml\n")

    return {
        **state,
        "current_phase":  "completado",
        "episode_number": episode_number,
        "rss_path":       str(RSS_OUTPUT),
        "publish_error":  None,
    }


def _extract_description(script: str) -> str:
    lines = [l.strip() for l in script.splitlines() if l.strip() and not l.startswith("[")]
    preview = " ".join(lines[:3])
    return preview[:300] + "..." if len(preview) > 300 else preview
