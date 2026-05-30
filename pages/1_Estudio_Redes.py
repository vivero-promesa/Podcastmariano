import streamlit as st
import google.generativeai as genai
import os
import sys

# Importamos tu motor de voz (Salomé) desde la carpeta de agentes
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.narrador import generar_audio

# 1. Configuración de la Página
st.set_page_config(page_title="Estudio de Redes", page_icon="📱", layout="wide")
st.title("📱 Estudio de Redes y Distribución")
st.markdown("Genera, edita y produce contenido viral con fidelidad al Magisterio de la Iglesia.")

# 2. Conexión y Buscador Automático de Modelos (Evita el Error 404)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Falta la llave de Gemini en los Secrets.")

def buscar_mejor_modelo():
    try:
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Preferimos la versión 1.5 Flash por velocidad, si no, Pro, si no, la que haya.
        for m in ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]:
            if m in modelos: return genai.GenerativeModel(m)
        return genai.GenerativeModel(modelos[0]) if modelos else None
    except:
        return None

# --- MÓDULO 1: KIT DE LANZAMIENTO ---
st.divider()
st.header("📦 Módulo 1: Kit de Lanzamiento (Spotify / YT)")

tema_kit = st.text_area("¿De qué trata el episodio?", height=80, key="input_kit")

if st.button("Generar Kit de Lanzamiento"):
    model = buscar_mejor_modelo()
    if model and tema_kit:
        with st.spinner("Creando títulos y hashtags católicos..."):
            prompt = f"Actúa como experto en marketing católico. Crea un kit para: {tema_kit}. Incluye: 3 títulos (intrigante, formativo, inspiracional), una descripción persuasiva y 10 hashtags SEO. REGLA: Tono reverente, fiel al Magisterio, cero lenguaje protestante o New Age."
            res = model.generate_content(prompt)
            st.session_state['kit_texto'] = res.text

# Editor Manual del Kit
if 'kit_texto' in st.session_state:
    st.subheader("📝 Edición Manual del Kit (Gratis)")
    kit_editado = st.text_area("Edita aquí tu kit:", value=st.session_state['kit_texto'], height=250)
    st.info("💡 Tip: Copia este texto y pégalo directamente en la descripción de tu episodio en Spotify.")

# --- MÓDULO 2: VIDEOS CORTOS (TIKTOK / REELS) ---
st.divider()
st.header("🎬 Módulo 2: Guion y Audio para TikTok")

guion_largo = st.text_area("Pega aquí el guion largo de tu podcast:", height=150, key="input_video")

if st.button("Extraer Guion de 60 Segundos"):
    model = buscar_mejor_modelo()
    if model and guion_largo:
        with st.spinner("Destilando el mensaje para video vertical..."):
            prompt_v = f"Resume este guion a 140 palabras (60 seg). Estructura: Gancho impactante, Desarrollo teológico y CTA. Escribe SOLO el texto que el narrador dirá. Guion: {guion_largo}"
            res_v = model.generate_content(prompt_v)
            st.session_state['guion_tiktok'] = res_v.text

# Editor Manual y Producción de Audio
if 'guion_tiktok' in st.session_state:
    st.subheader("📝 Revisa y Produce tu Video")
    guion_final = st.text_area("Guion final (Edítalo si es necesario):", value=st.session_state['guion_tiktok'], height=200)
    
    if st.button("🎙️ Generar Voz de Salomé para TikTok"):
        with st.spinner("Salomé está grabando tu cápsula para TikTok..."):
            # Generamos el audio usando el agente que ya tenemos
            nombre_audio = "tiktok_catolico.mp3"
            resultado = generar_audio(guion_final, nombre_audio)
            
            if resultado["success"]:
                st.success("✅ ¡Audio generado con éxito!")
                st.audio(resultado["ruta"])
                with open(resultado["ruta"], "rb") as f:
                    st.download_button("⬇️ Descargar MP3 para TikTok", f, file_name=nombre_archivo)
            else:
                st.error(f"Error en la voz: {resultado['error']}")
st.divider()

# --- MÓDULO 3: INSTAGRAM (CARRUSEL) ---
st.header("🎨 Módulo 3: Carrusel para Instagram")
st.markdown("Crea contenido educativo visual dividido en 5 diapositivas.")

guion_carrusel = st.text_area("Pega aquí el tema para el carrusel:", height=100, key="input_carrusel")

if st.button("Diseñar Carrusel"):
    if guion_carrusel:
        with st.spinner("Diseñando las diapositivas con rigor teológico..."):
            model = buscar_mejor_modelo()
            prompt_c = f"Actúa como experto en pedagogía católica. Crea un carrusel de 5 imágenes para Instagram sobre: {guion_carrusel}. Estructura: 1 Título gancho, 3 diapositivas de contenido doctrinal profundo pero sencillo, y 1 diapositiva de llamado a la acción. Escribe el texto para cada una de las 5 imágenes."
            res_c = model.generate_content(prompt_c)
            st.session_state['carrusel_texto'] = res_c.text

if 'carrusel_texto' in st.session_state:
    st.subheader("📝 Edita tus Diapositivas")
    texto_carrusel_final = st.text_area("Textos finales:", value=st.session_state['carrusel_texto'], height=300)
    st.info("💡 Tip: Copia estos textos y úsalos en Canva o tu herramienta de diseño preferida para crear las 5 imágenes.")
