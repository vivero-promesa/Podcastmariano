# 🌹 Cápsulas Marianas — Podcast Mariano AI

Sistema de producción automatizada de podcast católico mariano con agentes de IA.

## Flujo

```
Tema → Investigador → Censor Teológico → [Aprobación] → Guionista → ElevenLabs → MP3 → Spotify
```

## Instalación

```bash
git clone https://github.com/vivero-promesa/Podcastmariano.git
cd Podcastmariano
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edita .env con tus claves
```

## Uso

```bash
streamlit run streamlit_app.py
```

## RSS Feed (Spotify)

```
https://vivero-promesa.github.io/Podcastmariano/feed.xml
```

## Claves necesarias

- `GOOGLE_API_KEY` → https://aistudio.google.com/app/apikey
- `ELEVENLABS_API_KEY` → https://elevenlabs.io/app/settings/api-keys
