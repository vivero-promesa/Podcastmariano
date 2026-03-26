import os, json, shutil
from datetime import datetime, timezone
from pathlib import Path

PODCAST_CONFIG = {
    "title":       "Cápsulas Marianas",
    "description": "Episodios breves sobre misterios, advocaciones y espiritualidad mariana.",
    "author":      "Podcast Mariano AI",
    "email":       "tu-email@ejemplo.com",
    "website":     "https://vivero-promesa.github.io/Podcastmariano",
    "image_url":   "https://vivero-promesa.github.io/Podcastmariano/cover.jpg",
    "language":    "es",
    "category":    "Religion &amp; Spirituality",
    "explicit":    "false",
}
EPISODES_DB   = Path("data/episodes.json")
RSS_OUTPUT    = Path("docs/feed.xml")
AUDIO_WEBROOT = "{website}/audio"

def _load_episodes():
    if EPISODES_DB.exists():
        with open(EPISODES_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def _save_episodes(episodes):
    EPISODES_DB.parent.mkdir(parents=True, exist_ok=True)
    with open(EPISODES_DB, "w", encoding="utf-8") as f:
        json.dump(episodes, f, ensure_ascii=False, indent=2)

def _rfc2822_now():
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

def _episode_to_item(ep, cfg):
    audio_url = AUDIO_WEBROOT.format(website=cfg["website"]) + "/" + ep["filename"]
    return f"""
    <item>
      <title>{ep['title']}</title>
      <description><![CDATA[{ep['description']}]]></description>
      <pubDate>{ep['pub_date']}</pubDate>
      <guid isPermaLink="false">{ep['guid']}</guid>
      <enclosure url="{audio_url}" length="{ep['size_bytes']}" type="audio/mpeg"/>
      <itunes:duration>{ep.get('duration','00:02:30')}</itunes:duration>
      <itunes:episode>{ep['episode_number']}</itunes:episode>
    </item>"""

def _build_rss(episodes, cfg):
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
    <itunes:image href="{cfg['image_url']}"/>
    <itunes:category text="{cfg['category']}"/>
    <itunes:explicit>{cfg['explicit']}</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    {items}
  </channel>
</rss>"""

def publisher_agent(state: dict) -> dict:
    print("📡 [Publisher] Registrando episodio...")
    audio_path = state.get("audio_path", "")
    topic      = state.get("topic", "Episodio sin título")
    script     = state.get("script", "")
    if not audio_path or not Path(audio_path).exists():
        return {**state, "publish_error": f"Audio no encontrado: {audio_path}"}
    episodes       = _load_episodes()
    episode_number = len(episodes) + 1
    filename       = Path(audio_path).name
    audio_dest     = Path("docs/audio")
    audio_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(audio_path, audio_dest / filename)
    lines   = [l.strip() for l in script.splitlines() if l.strip() and not l.startswith("[")]
    preview = " ".join(lines[:3])[:300]
    episode = {
        "episode_number": episode_number,
        "guid":    f"capsulas-marianas-ep-{episode_number:03d}",
        "title":   f"Ep. {episode_number:03d} — {topic}",
        "description": preview,
        "filename": filename,
        "audio_path": str(audio_dest / filename),
        "size_bytes": os.path.getsize(str(audio_dest / filename)),
        "duration": "00:02:30",
        "pub_date": _rfc2822_now(),
        "topic": topic,
    }
    episodes.append(episode)
    _save_episodes(episodes)
    RSS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    RSS_OUTPUT.write_text(_build_rss(episodes, PODCAST_CONFIG), encoding="utf-8")
    print(f"✅ Episodio #{episode_number} publicado. Haz git push.")
    print(f"   RSS: {PODCAST_CONFIG['website']}/feed.xml")
    return {**state, "current_phase": "completado", "episode_number": episode_number, "publish_error": None}
