# 🎙️ La maternidad no siempre tiene cuna; a veces tiene cruz — Estudio con IA

Sistema de producción del podcast católico **«La maternidad no siempre tiene cuna; a veces tiene cruz»** (bioética, fertilidad y dignidad humana desde la doctrina católica) y de sus redes **@cienciamasconciencia**.

- Spotify: https://open.spotify.com/show/6FEnSg3Ee7THgmFLuQRiIW
- Instagram y TikTok: @cienciamasconciencia

> Antes se llamaba «Cápsulas Marianas». Esta versión reemplaza ese flujo.

## Regla de oro

Cada tarea se hace en un solo lugar. Los títulos, la descripción, los hashtags, los clips y sus textos salen de esta app; no se rehacen en otra herramienta.

## Flujo semanal

1. Documento de la Iglesia (texto oficial de vatican.va)
2. **Investigadora** (Gemini): cita solo lo que está en el documento
3. **Censor Doctrinal**: verifica las citas contra el texto oficial
4. ✅ Primera aprobación de la Directora
5. **Guionista**: episodio de 15-20 min con 5 momentos [CLIP]
6. **Censor Doctrinal** del guion
7. ✅ Segunda aprobación de la Directora
8. **Paquete de publicación**: títulos para el buscador, descripción, hashtags y portada
9. Grabas con tu voz
10. **Estudio de Redes**: clips 9:16 con gancho, subtítulos, «Episodio completo en Spotify» y sus textos para Instagram y TikTok
11. Publicas en Spotify el viernes y programas 3 clips

| Día | Qué haces | Dónde |
| --- | --- | --- |
| Lunes | Investigación, guion y las dos aprobaciones | Estudio de producción |
| Martes | Grabar con tu voz | Tu micrófono |
| Miércoles | Clips y capítulos; eliges los 3 mejores | Estudio de Redes |
| Jueves | Portada y programar los 3 clips (unos 45 min) | Instagram y TikTok Studio |
| Viernes | Publicar en Spotify y poner el enlace del episodio en las bios | Spotify for Creators, Instagram, TikTok |
| Fin de semana | Responder comentarios | Instagram, TikTok, Spotify |

### Redes: modelo vigente (octubre 2026)

- **3 clips por semana.** El mismo archivo va a Instagram (prioridad) y a TikTok.
- Sin Facebook. Instagram se programa desde su propia app; TikTok desde TikTok Studio.
- Los textos de cada clip empiezan con una pregunta real y terminan invitando a comentar; nunca «nuevo episodio».
- En Instagram, si la cuenta tiene la opción, publica los clips como **Reel de prueba (Trial Reel)**: primero los ve gente que aún no te sigue.
- **En pausa:** carrusel semanal, imágenes con cita, Historias diarias y cápsula con voz IA. El código sigue en la app por si se retoman.

## Páginas

- **Estudio de producción** (`paginas/produccion.py`): documento → investigación → censor → guion → censor → paquete (.zip).
- **Estudio de Redes** (`paginas/redes.py`):
  - 🎬 **Clips del episodio**: subes el audio, la IA elige los mejores momentos (30-90 s) y arma videos con subtítulos y sus textos. Opcional: pega el enlace del episodio para que los textos lo usen. También da los capítulos para Spotify.
  - 🔤 **Títulos para el buscador**: reescribe los títulos de episodios ya publicados.
  - ⏸️ **Carrusel** y ⏸️ **Cápsula con voz IA**: en pausa.

## Instalación

### Opción A — Streamlit Community Cloud (recomendada)

1. En https://share.streamlit.io crea la app desde este repositorio, archivo `streamlit_app.py`.
2. En **Advanced settings** elige **Python 3.12** (con 3.14 algunas librerías, como pyarrow, aún fallan). Streamlit Cloud solo deja elegir la versión al crear la app: si ya existe con otra versión, bórrala y vuelve a crearla.
3. En **Settings → Secrets** agrega:

```toml
GOOGLE_API_KEY = "tu-clave"
```

No agregues `GEMINI_MODEL` salvo que quieras otro modelo: por defecto se usa `gemini-3.8-flash`.

`packages.txt` instala ffmpeg automáticamente.

### Opción B — Codespaces o tu computador

```bash
git clone https://github.com/vivero-promesa/Podcastmariano.git
cd Podcastmariano
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # y pon tu GOOGLE_API_KEY
streamlit run streamlit_app.py
```

Necesitas ffmpeg instalado (en Codespaces se instala solo con `packages.txt`).

### Consola (sin interfaz)

```bash
python main.py
```

## Claves

| Variable | Para qué | Dónde se saca |
| --- | --- | --- |
| `GOOGLE_API_KEY` | Gemini (investigación, censor, guion, clips) | https://aistudio.google.com/app/apikey |
| `GEMINI_MODEL` | Opcional, por defecto `gemini-3.8-flash` | — |
| `VOZ_IA` | Opcional, por defecto `es-CO-SalomeNeural` | — |

## Qué sigue siendo manual (a propósito)

- Grabar el episodio con tu voz.
- Subir el audio a Spotify for Creators: Spotify no ofrece una API pública para publicar episodios.
- Programar los clips en Instagram y TikTok.
- Las dos aprobaciones de la Directora: ningún contenido avanza sin tu visto bueno.

## Estructura

| Archivo | Qué hace |
| --- | --- |
| `streamlit_app.py` | Menú de páginas y barra lateral común |
| `paginas/produccion.py` | Estudio de producción |
| `paginas/redes.py` | Estudio de Redes |
| `paginas/comun.py` | Barra lateral, revisión del Censor y aprobaciones |
| `config.py` | Identidad del programa, enlaces, documentos, modelo y clips por semana |
| `agents/llm.py` | Conexión con Gemini (SDK google-genai, salidas estructuradas) |
| `agents/fuentes.py` | Descarga del texto oficial desde vatican.va |
| `agents/investigator.py` | Investigadora |
| `agents/theologian.py` | Censor doctrinal (investigación y guion) |
| `agents/script_writer.py` | Guionista |
| `agents/publicacion.py` | Títulos, descripción, hashtags |
| `agents/clips.py` | Selección de momentos, subtítulos y textos de cada clip |
| `agents/video.py` | ffmpeg: cortes y videos 9:16 |
| `agents/carrusel.py` | Carrusel para Canva (en pausa) |
| `agents/narrador.py` | Voz IA con edge-tts (en pausa) |
