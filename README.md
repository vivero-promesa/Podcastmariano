# 🎙️ La maternidad no siempre tiene cuna — Estudio con IA

Sistema de producción del podcast católico **«La maternidad no siempre tiene cuna, a veces es una cruz»**
(bioética, fertilidad y dignidad humana desde la doctrina católica) y de sus redes **@cienciamasconciencia**.

- Spotify: https://open.spotify.com/show/6FEnSg3Ee7THgmFLuQRiIW
- Instagram y TikTok: @cienciamasconciencia

> Antes se llamaba «Cápsulas Marianas». Esta versión 2 reemplaza ese flujo.

## Flujo semanal

```
Documento de la Iglesia (texto oficial de vatican.va)
   → Investigadora (Gemini)          cita solo lo que está en el documento
   → Censor Doctrinal                verifica citas contra el texto oficial
   → ✅ Aprobación de la Directora
   → Guionista                       episodio de 15-20 min + 5 momentos [CLIP]
   → Censor Doctrinal del guion      corrige automáticamente si hace falta
   → ✅ Aprobación de la Directora
   → Paquete de publicación          títulos para el buscador, descripción, hashtags, portada
   → Grabas con tu voz y subes a Spotify for Creators (viernes)
   → Estudio de Redes                5 videos 9:16 con gancho, subtítulos y «Episodio completo en Spotify»
```

| Día | Qué haces | Dónde |
|---|---|---|
| Lunes | Investigación + guion | Página principal |
| Martes | Grabar con tu voz | Tu micrófono |
| Miércoles | Subir a Spotify for Creators y programar para el viernes | Spotify for Creators |
| Jueves | Clips, carrusel y textos | Estudio de Redes |
| Viernes | Publicar en Spotify, Instagram y TikTok | Apps |

## Páginas

1. **Estudio de producción** (`paginas/produccion.py`): documento → investigación → censor → guion → censor → paquete (.zip).
2. **Estudio de Redes** (`paginas/redes.py`):
   - 🎬 Clips del episodio: sube el audio, la IA elige los mejores momentos y arma videos con subtítulos. También da los capítulos para Spotify.
   - 🔤 Títulos para el buscador: reescribe los títulos de los episodios ya publicados.
   - 🎨 Carrusel para Canva: CSV para Bulk Create + caption.
   - 🗣️ Cápsula con voz IA: video de 60 s sin grabar.

## Instalación

### Opción A — Streamlit Community Cloud (recomendada)
1. En https://share.streamlit.io crea la app desde este repositorio, archivo `streamlit_app.py`.
2. En **Advanced settings** elige **Python 3.12** (con 3.14 algunas librerías, como pyarrow, aún fallan).
   Streamlit Cloud solo deja elegir la versión al crear la app: si ya existe con otra versión, bórrala y vuelve a crearla.
3. En **Settings → Secrets** agrega:
   ```toml
   GOOGLE_API_KEY = "tu-clave"
   ```
4. `packages.txt` instala ffmpeg automáticamente.

### Opción B — Codespaces o tu computador
```bash
git clone https://github.com/vivero-promesa/Podcastmariano.git
cd Podcastmariano
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # y pon tu GOOGLE_API_KEY
streamlit run streamlit_app.py
```
Necesitas ffmpeg instalado (en Codespaces se instala solo con `packages.txt`).

### Consola (sin interfaz)
```bash
python main.py
```

## Claves

| Variable | Para qué | Dónde se saca |
|---|---|---|
| `GOOGLE_API_KEY` | Gemini (investigación, censor, guion, clips) | https://aistudio.google.com/app/apikey |
| `GEMINI_MODEL` | Opcional, por defecto `gemini-2.5-flash` | — |
| `VOZ_IA` | Opcional, por defecto `es-CO-SalomeNeural` | — |

## Qué sigue siendo manual (a propósito)

- **Grabar** el episodio con tu voz.
- **Subir** el MP3 a Spotify for Creators: Spotify no ofrece una API pública para publicar episodios.
- **Publicar** los clips en TikTok e Instagram (o programarlos en Meta Business Suite).
- Las dos **aprobaciones** de la Directora: ningún contenido avanza sin tu visto bueno.

## Estructura

```
streamlit_app.py          menú de páginas y barra lateral común
paginas/produccion.py     Estudio de producción
paginas/redes.py          Estudio de Redes
paginas/comun.py          barra lateral, revisión del Censor y aprobaciones
config.py                 identidad del programa, enlaces, documentos y modelo
agents/llm.py             conexión con Gemini (SDK google-genai, salidas estructuradas)
agents/fuentes.py         descarga del texto oficial desde vatican.va
agents/investigator.py    investigadora
agents/theologian.py      censor doctrinal (investigación y guion)
agents/script_writer.py   guionista
agents/publicacion.py     títulos, descripción, hashtags
agents/clips.py           selección de momentos y subtítulos
agents/video.py           ffmpeg: cortes y videos 9:16
agents/carrusel.py        carrusel para Canva
agents/narrador.py        voz IA (edge-tts)
```
