# 🎙️ La maternidad no siempre tiene cuna; a veces tiene cruz — Estudio con IA

Sistema de producción del podcast católico **«La maternidad no siempre tiene cuna; a veces tiene cruz»** (bioética, fertilidad y dignidad humana desde la doctrina católica) y de sus redes **@cienciamasconciencia**.

- Spotify: https://open.spotify.com/show/6FEnSg3Ee7THgmFLuQRiIW
- Instagram y TikTok: @cienciamasconciencia

> Antes se llamaba «Cápsulas Marianas». Esta versión reemplaza ese flujo.

## Regla de oro

Cada tarea se hace en un solo lugar. Los enfoques, la investigación, el guion, los títulos, la descripción, los hashtags, los clips y sus textos salen de esta app; no se rehacen en otra herramienta.

## Flujo semanal

1. Eliges **uno, dos o tres documentos** de la Iglesia (texto oficial de vatican.va). Combinarlos sirve para mostrar cómo evolucionó la enseñanza, por ejemplo Donum Vitae + Dignitas Personae.
2. **Enfoques nuevos**: la app propone al menos 3 preguntas para el episodio, evitando lo que ya se trató según el historial.
3. **Investigadora** (Gemini): cita solo lo que está en los documentos e indica de cuál sale cada cita
4. **Censor Doctrinal**: verifica cada cita contra el texto oficial del documento que dice citar
5. ✅ Primera aprobación de la Directora
6. **Guionista**: episodio de 15-20 min con 5 momentos [CLIP]
7. **Censor Doctrinal** del guion
8. ✅ Segunda aprobación de la Directora
9. **Paquete de publicación**: títulos para el buscador, descripción, hashtags y portada
10. **Historial**: guardas el episodio con su enfoque y los puntos que profundizó
11. Grabas con tu voz
12. **Estudio de Redes**: clips 9:16 con gancho, subtítulos, «Episodio completo en Spotify» y sus textos para Instagram y TikTok
13. Publicas en Spotify el viernes y programas 3 clips

| Día | Qué haces | Dónde |
| --- | --- | --- |
| Lunes | Documento(s), enfoque, investigación, guion, las dos aprobaciones y guardar en el historial | Estudio de producción |
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

- **Estudio de producción** (`paginas/produccion.py`):
  - 🆕 **Buscar documentos nuevos**: revisa en vatican.va las encíclicas, exhortaciones, cartas apostólicas y motu proprio de León XIV y los documentos del Dicasterio para la Doctrina de la Fe desde 2020. Muestra solo los que tratan la vida, la familia o la bioética y no están en el catálogo, y los agrega con un clic.
  - Documento(s) → enfoques → investigación → censor → guion → censor → paquete (.zip) → historial.
  - 📖 **Historial de episodios**: todos los episodios con sus documentos y los puntos profundizados.
- **Estudio de Redes** (`paginas/redes.py`):
  - 🎬 **Clips del episodio**: subes el audio, la IA elige los mejores momentos (30-90 s) y arma videos con subtítulos y sus textos. Opcional: pega el enlace del episodio para que los textos lo usen. También da los capítulos para Spotify.
    - Video: subtítulos grandes estilo Reels (3-4 palabras, la palabra clave en dorado), todo dentro de la zona que no tapan los botones de Instagram y TikTok, volumen parejo (-14 LUFS), movimiento suave de la foto y portada JPG de cada clip.
    - 🎨 **Imagen con IA por clip**: la IA propone una escena para cada momento y Gemini la pinta en vertical (estilo editorial católico, sin texto). Puedes editar la idea, rehacerla o subir tu propia foto (tiene prioridad).
    - 🚀 **Publicar en Instagram y TikTok** con un botón (ver «Publicar desde la app»). Sin conexión, la app deja descargar y abrir cada red para subirlo a mano.
  - 🔤 **Títulos para el buscador**: reescribe los títulos de episodios ya publicados.
  - ⏸️ **Carrusel** y ⏸️ **Cápsula con voz IA**: en pausa.

## Historial y catálogo (`historial_episodios.json`)

El historial de episodios y los documentos agregados desde la app viven en `historial_episodios.json`, en este mismo repositorio. Así no se pierden cuando Streamlit Cloud reinicia la app, y cada guardado queda como un commit.

- Los documentos fijos están en `config.py`; los que agregas con «Buscar documentos nuevos» quedan en `documentos_extra`.
- Para que la app guarde sola, agrega `GITHUB_TOKEN` en los Secrets (ver **Claves**). Sin token, la app te deja descargar el archivo actualizado para subirlo a mano.

## Instalación

### Opción A — Streamlit Community Cloud (recomendada)

1. En https://share.streamlit.io crea la app desde este repositorio, archivo `streamlit_app.py`.
2. En **Advanced settings** elige **Python 3.12** (con 3.14 algunas librerías, como pyarrow, aún fallan). Streamlit Cloud solo deja elegir la versión al crear la app: si ya existe con otra versión, bórrala y vuelve a crearla.
3. En **Settings → Secrets** agrega:

```toml
GOOGLE_API_KEY = "tu-clave-de-gemini"
GITHUB_TOKEN = "tu-token-de-github"
```

No agregues `GEMINI_MODEL` salvo que quieras otro modelo: por defecto se usa `gemini-3.8-flash`.

`packages.txt` instala ffmpeg automáticamente.

### Cómo crear el GITHUB_TOKEN

1. Entra a GitHub con la cuenta dueña del repositorio (**vivero-promesa**).
2. Ve a **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
3. Nombre: `Podcastmariano historial`. Resource owner: **vivero-promesa**. Expiración: 1 año.
4. **Repository access → Only select repositories →** `Podcastmariano`.
5. **Permissions → Repository permissions → Contents → Read and write**. Nada más.
6. Copia el token y pégalo en los Secrets de Streamlit como `GITHUB_TOKEN`. No lo pegues en chats ni documentos.

### Opción B — Codespaces o tu computador

```bash
git clone https://github.com/vivero-promesa/Podcastmariano.git
cd Podcastmariano
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # y pon tu GOOGLE_API_KEY (y GITHUB_TOKEN si quieres guardar el historial)
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
| `GOOGLE_API_KEY` | Gemini (enfoques, investigación, censor, guion, clips) | https://aistudio.google.com/app/apikey |
| `GITHUB_TOKEN` | Guardar el historial y los documentos nuevos en este repositorio | GitHub → Fine-grained token con Contents: Read and write (ver arriba) |
| `GEMINI_MODEL` | Opcional, por defecto `gemini-3.8-flash` | — |
| `VOZ_IA` | Opcional, por defecto `es-CO-SalomeNeural` | — |
| `GEMINI_MODELO_IMAGEN` | Opcional: modelos de Gemini para imágenes, separados por comas. Si no responden, la app busca uno disponible | — |
| `INSTAGRAM_TOKEN` / `INSTAGRAM_USER_ID` | Botón Publicar: Instagram (el ID solo con token `EAA…`) | Ver «Publicar desde la app» |
| `TIKTOK_CLIENT_KEY` / `TIKTOK_CLIENT_SECRET` / `TIKTOK_REDIRECT_URI` / `TIKTOK_REFRESH_TOKEN` / `TIKTOK_MODO` | Botón Publicar: TikTok | Ver «Publicar desde la app» |
| `GITHUB_REPO` / `GITHUB_BRANCH` | Opcionales, por defecto `vivero-promesa/Podcastmariano` y `main` | — |

## Publicar desde la app (Instagram y TikTok)

El botón **🚀 Publicar** de cada clip sube el mismo video a las dos redes con su texto. Cada red se conecta una sola vez; si una no está conectada, el botón publica solo en la otra.

### Instagram (no necesita Facebook ni página de Facebook)

Usa la «API de Instagram con inicio de sesión de Instagram». Requisitos: la cuenta @cienciamasconciencia debe ser **profesional** (Creador o Empresa), que se cambia gratis en la app de Instagram → Configuración → Tipo de cuenta.

1. Entra a https://developers.facebook.com → **Mis apps → Crear app** → caso de uso **«Administrar mensajes y contenido en Instagram»**. (Meta puede pedir entrar con una cuenta de Meta para registrarte como desarrolladora; el podcast sigue sin usar Facebook.)
2. En **Instagram → Configuración de la API con inicio de sesión de Instagram** → **Generar tokens de acceso** → **Agregar cuenta** e inicia sesión con @cienciamasconciencia.
3. Copia el token y pégalo en **Settings → Secrets** de Streamlit:

```toml
INSTAGRAM_TOKEN = "IGAA…"
```

**Si Meta solo te deja el «inicio de sesión unificado»** (apps nuevas): crea la configuración en Casos de uso → API de Instagram, genera un token de usuario del sistema (empieza por `EAA…`, no vence) y agrega también el ID de la cuenta de Instagram:

```toml
INSTAGRAM_TOKEN = "EAA…"
INSTAGRAM_USER_ID = "123456789"
```

El token `IGAA…` dura **60 días**. Antes de que venza, en la app usa **🔌 Conexión → 🔄 Renovar token** y pega el nuevo en los Secrets.

Cómo publica: Instagram descarga el video desde una dirección pública, así que la app lo sube un momento a `litterbox.catbox.moe` (se borra solo en 1 hora), crea el Reel, espera a que Instagram lo procese y lo publica. Si marcas **Reel de prueba** y tu cuenta lo admite, se muestra primero a quien aún no te sigue.

Mientras la app de Meta esté en «modo desarrollo» solo publica en las cuentas agregadas en el paso 2, que es justo lo que se necesita: no hace falta revisión de Meta.

### TikTok

1. Entra a https://developers.tiktok.com con la cuenta @cienciamasconciencia → **Manage apps → Connect an app**.
2. Agrega los productos **Login Kit** y **Content Posting API** (activa «Direct Post» si más adelante quieres publicar directo).
3. En **Login Kit → Redirect URI** pon la dirección de la página de Redes, por ejemplo `https://tu-app.streamlit.app/redes`.
4. Permisos (scopes): `user.info.basic`, `video.upload`, `video.publish`.
5. Para probar sin revisión usa **Sandbox** y agrega @cienciamasconciencia como usuario de prueba (Target users).
6. Pega en los Secrets:

```toml
TIKTOK_CLIENT_KEY = "…"
TIKTOK_CLIENT_SECRET = "…"
TIKTOK_REDIRECT_URI = "https://tu-app.streamlit.app/redes"
TIKTOK_MODO = "borrador"
```

7. En la app: **Estudio de Redes → 🔌 Conexión → 🔗 Conectar TikTok**. Al volver, la app muestra un código: pégalo en los Secrets como `TIKTOK_REFRESH_TOKEN` (dura 1 año).

Modos:

- **`borrador`** (recomendado al comienzo): el video llega a tu bandeja de TikTok (notificaciones). Abres TikTok, pegas el texto, eliges sonido o portada si quieres, y publicas. Funciona sin auditoría.
- **`directo`**: se publica con el texto de una vez. TikTok solo lo permite en público después de **auditar** la app; antes de eso solo deja publicar como privado.

## Qué sigue siendo manual (a propósito)

- Grabar el episodio con tu voz.
- Subir el audio a Spotify for Creators: Spotify no ofrece una API pública para publicar episodios.
- Programar los clips para otro día: el botón publica en el momento. Para dejar un clip programado, usa la app de Instagram o TikTok Studio.
- Las dos aprobaciones de la Directora: ningún contenido avanza sin tu visto bueno.

## Estructura

| Archivo | Qué hace |
| --- | --- |
| `streamlit_app.py` | Menú de páginas y barra lateral común |
| `paginas/produccion.py` | Estudio de producción |
| `paginas/redes.py` | Estudio de Redes |
| `paginas/comun.py` | Barra lateral, revisión del Censor y aprobaciones |
| `config.py` | Identidad del programa, enlaces, documentos fijos, modelo y clips por semana |
| `historial_episodios.json` | Historial de episodios y documentos agregados al catálogo |
| `agents/llm.py` | Conexión con Gemini (SDK google-genai, salidas estructuradas) |
| `agents/fuentes.py` | Descarga del texto oficial desde vatican.va |
| `agents/historial.py` | Leer y guardar el historial en GitHub |
| `agents/enfoques.py` | Enfoques nuevos para el episodio y puntos profundizados |
| `agents/novedades.py` | Búsqueda de documentos nuevos del Papa y de la Santa Sede |
| `agents/investigator.py` | Investigadora (uno o varios documentos) |
| `agents/theologian.py` | Censor doctrinal (investigación y guion, cita por cita y documento por documento) |
| `agents/script_writer.py` | Guionista |
| `agents/publicacion.py` | Títulos, descripción, hashtags |
| `agents/clips.py` | Selección de momentos, subtítulos y textos de cada clip |
| `agents/video.py` | ffmpeg: cortes, volumen parejo, subtítulos estilo Reels y videos 9:16 |
| `agents/imagenes.py` | Imágenes con IA (Gemini) para clips y carrusel |
| `agents/publicar_redes.py` | Publicación en Instagram (Reel) y TikTok |
| `agents/carrusel_imagenes.py` | Diapositivas del carrusel como imágenes |
| `agents/carrusel.py` | Carrusel para Canva (en pausa) |
| `agents/narrador.py` | Voz IA con edge-tts (en pausa) |
