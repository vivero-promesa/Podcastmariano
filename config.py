"""Configuración central del podcast «La maternidad no siempre tiene cuna».

Todo lo que identifica al programa (nombre, enlaces, voz, modelo de IA y
catálogo de documentos del Magisterio) vive aquí, para cambiarlo en un solo lugar.
"""
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv es opcional en Streamlit Cloud
    pass


def _secreto(nombre: str, defecto: str = "") -> str:
    """Lee primero variables de entorno (.env / Codespaces) y luego st.secrets (Streamlit Cloud)."""
    valor = os.getenv(nombre)
    if valor:
        return valor
    try:
        import streamlit as st

        return str(st.secrets.get(nombre, defecto))
    except Exception:
        return defecto


def api_key() -> str:
    return _secreto("GOOGLE_API_KEY") or _secreto("GEMINI_API_KEY")


# Modelo de Gemini. Se puede cambiar sin tocar código con la variable GEMINI_MODEL.
# gemini-3.8-flash es el Flash estable desde septiembre de 2026; Google limitó el acceso
# a los modelos 2.5 a quienes ya los usaban, así que una clave nueva podría fallar con 2.5.
MODELO = _secreto("GEMINI_MODEL", "gemini-3.8-flash")
# Respaldos en orden si el modelo principal está saturado (503), separados por comas.
# El "lite" usa otra capacidad de Google y casi siempre responde. Se cambia con GEMINI_MODEL_RESPALDO.
MODELO_RESPALDO = _secreto("GEMINI_MODEL_RESPALDO", "gemini-flash-latest,gemini-flash-lite-latest")

# Modelos de Gemini que crean imágenes (fondos de clips y carrusel), en orden. Si ninguno
# responde, la app busca sola uno disponible en tu cuenta. Se cambia con GEMINI_MODELO_IMAGEN.
MODELO_IMAGEN = _secreto("GEMINI_MODELO_IMAGEN", "gemini-2.5-flash-image,gemini-3-pro-image-preview")

# ─────────────────────────────────────────────────────────────
# Publicación directa en redes (opcional; sin estas claves la app usa el modo manual)
# ─────────────────────────────────────────────────────────────
# Instagram: token «IGAA…» (inicio de sesión de Instagram) o token de usuario del sistema «EAA…»
# (inicio de sesión unificado). Con «EAA…» hace falta INSTAGRAM_USER_ID, el ID de la cuenta de Instagram.
INSTAGRAM_TOKEN = _secreto("INSTAGRAM_TOKEN")
INSTAGRAM_USER_ID = _secreto("INSTAGRAM_USER_ID")
INSTAGRAM_API_VERSION = _secreto("INSTAGRAM_API_VERSION", "v23.0")
# TikTok: app de TikTok for Developers con Content Posting API.
TIKTOK_CLIENT_KEY = _secreto("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = _secreto("TIKTOK_CLIENT_SECRET")
TIKTOK_REFRESH_TOKEN = _secreto("TIKTOK_REFRESH_TOKEN")
# Dirección de esta página tal como está registrada en TikTok (Redirect URI), p. ej.
# https://tu-app.streamlit.app/redes
TIKTOK_REDIRECT_URI = _secreto("TIKTOK_REDIRECT_URI")
# «borrador»: el video llega a tu bandeja de TikTok y tú lo publicas desde la app (funciona sin auditoría).
# «directo»: se publica de una vez (TikTok lo permite en público solo cuando aprueba la auditoría de la app).
TIKTOK_MODO = _secreto("TIKTOK_MODO", "borrador").strip().lower()

# ─────────────────────────────────────────────────────────────
# Identidad del programa
# ─────────────────────────────────────────────────────────────
PODCAST = {
    "nombre": "La maternidad no siempre tiene cuna; a veces tiene cruz",
    "nombre_corto": "La maternidad no siempre tiene cuna",
    "descripcion": (
        "Bioética, fertilidad y dignidad humana desde la doctrina católica. "
        "Cada semana leemos un documento de la Iglesia y lo explicamos con palabras de a pie."
    ),
    "spotify": "https://open.spotify.com/show/6FEnSg3Ee7THgmFLuQRiIW",
    "instagram": "@cienciamasconciencia",
    "instagram_url": "https://www.instagram.com/cienciamasconciencia",
    "tiktok": "@cienciamasconciencia",
    "tiktok_url": "https://www.tiktok.com/@cienciamasconciencia",
    "hashtag_marca": "#LaMaternidadNoSiempreTieneCuna",
    "audiencia": "adultos católicos de 30 a 50 años, sobre todo en México y Colombia",
    "llamado_spotify": "Escucha el episodio completo en Spotify (enlace en la bio)",
}

# Modelo de publicación vigente (oct 2026): 3 clips por semana, el mismo archivo en
# Instagram (prioridad) y TikTok. Sin Facebook. Carrusel y cápsula con voz IA en pausa.
CLIPS_POR_SEMANA = 3

# Voz gratuita para borradores y cápsulas cortas (edge-tts).
VOZ_IA = _secreto("VOZ_IA", "es-CO-SalomeNeural")

# Palabras que la gente realmente escribe en el buscador (diagnóstico Spotify, oct 2026).
PALABRAS_BUSQUEDA = [
    "FIV",
    "fecundación in vitro",
    "in vitro",
    "¿es pecado?",
    "infertilidad",
    "infertilidad católica",
    "embriones congelados",
    "vientre de alquiler",
    "anticonceptivos",
    "Iglesia católica",
]

# ─────────────────────────────────────────────────────────────
# Catálogo de documentos (calendario editorial de 12 semanas)
# Las URL son las versiones oficiales en español de vatican.va.
# ─────────────────────────────────────────────────────────────
DOCUMENTOS = [
    {
        "clave": "DV",
        "titulo": "Donum Vitae",
        "anio": 1987,
        "tema": "FIV y el embrión como persona",
        "url": "https://www.vatican.va/roman_curia/congregations/cfaith/documents/rc_con_cfaith_doc_19870222_respect-for-human-life_sp.html",
    },
    {
        "clave": "EV",
        "titulo": "Evangelium Vitae",
        "anio": 1995,
        "tema": "Cultura de la vida frente a cultura de la muerte",
        "url": "https://www.vatican.va/content/john-paul-ii/es/encyclicals/documents/hf_jp-ii_enc_25031995_evangelium-vitae.html",
    },
    {
        "clave": "DP",
        "titulo": "Dignitas Personae",
        "anio": 2008,
        "tema": "Clonación, células madre, embriones congelados y diagnóstico preimplantatorio",
        "url": "https://www.vatican.va/roman_curia/congregations/cfaith/documents/rc_con_cfaith_doc_20081208_dignitas-personae_sp.html",
    },
    {
        "clave": "GS",
        "titulo": "Gaudium et Spes (n. 14 «Corpore et anima unus» y n. 51)",
        "anio": 1965,
        "tema": "Unidad cuerpo-alma, matrimonio y procreación",
        "url": "https://www.vatican.va/archive/hist_councils/ii_vatican_council/documents/vat-ii_const_19651207_gaudium-et-spes_sp.html",
    },
    {
        "clave": "HV",
        "titulo": "Humanae Vitae",
        "anio": 1968,
        "tema": "Anticoncepción y apertura a la vida",
        "url": "https://www.vatican.va/content/paul-vi/es/encyclicals/documents/hf_p-vi_enc_25071968_humanae-vitae.html",
    },
    {
        "clave": "FC",
        "titulo": "Familiaris Consortio",
        "anio": 1981,
        "tema": "Familia y matrimonio",
        "url": "https://www.vatican.va/content/john-paul-ii/es/apost_exhortations/documents/hf_jp-ii_exh_19811122_familiaris-consortio.html",
    },
    {
        "clave": "CV",
        "titulo": "Caritas in Veritate",
        "anio": 2009,
        "tema": "Ética de la tecnología",
        "url": "https://www.vatican.va/content/benedict-xvi/es/encyclicals/documents/hf_ben-xvi_enc_20090629_caritas-in-veritate.html",
    },
    {
        "clave": "LS",
        "titulo": "Laudato Si'",
        "anio": 2015,
        "tema": "Ecología humana y tecnociencia",
        "url": "https://www.vatican.va/content/francesco/es/encyclicals/documents/papa-francesco_20150524_enciclica-laudato-si.html",
    },
    {
        "clave": "VS",
        "titulo": "Veritatis Splendor",
        "anio": 1993,
        "tema": "Moral objetiva",
        "url": "https://www.vatican.va/content/john-paul-ii/es/encyclicals/documents/hf_jp-ii_enc_06081993_veritatis-splendor.html",
    },
    {
        "clave": "AL",
        "titulo": "Amoris Laetitia",
        "anio": 2016,
        "tema": "Parejas con infertilidad y el amor en la familia",
        "url": "https://www.vatican.va/content/francesco/es/apost_exhortations/documents/papa-francesco_esortazione-ap_20160319_amoris-laetitia.html",
    },
    {
        "clave": "CIC",
        "titulo": "Catecismo de la Iglesia Católica §2258-2330",
        "anio": 1992,
        "tema": "Quinto mandamiento: respeto a la vida humana",
        "url": "https://www.vatican.va/archive/catechism_sp/p3s2c2a5_sp.html",
    },
]

TEMA_LIBRE = {"clave": "LIBRE", "titulo": "Tema libre (sin documento)", "anio": None, "tema": "", "url": ""}


def etiqueta_documento(doc: dict) -> str:
    if doc["clave"] == "LIBRE":
        return doc["titulo"]
    return f"{doc['titulo']} ({doc['anio']}) — {doc['tema']}"
