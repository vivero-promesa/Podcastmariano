import streamlit as st
import google.generativeai as genai
import os
import sys
import pandas as pd

# Importamos el motor de voz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.narrador import generar_audio

# Configuración
st.set_page_config(page_title="Estudio de Redes", page_icon="📱", layout="wide")
st.title("📱 Estudio de Redes y Distribución")

def buscar_mejor_modelo():
    try:
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]:
            if m in modelos: return genai.GenerativeModel(m)
        return genai.GenerativeModel(modelos[0]) if modelos else None
    except: return None

# --- MÓDULO 1: KIT DE LANZAMIENTO ---
st.header("📦 Módulo 1: Kit de Lanzamiento")
tema_kit = st.text_area("¿De qué trata el episodio?", height=80, key="kit")
if st.button("Generar Kit"):
    model = buscar_mejor_modelo()
    if model:
        res = model.generate_content(f"Crea un kit católico para: {tema_kit}. 3 títulos, descripción y 10 hashtags.")
        st.session_state['kit_texto'] = res.text
if 'kit_texto' in st.session_state:
    st.text_area("Edita tu kit:", value=st.session_state['kit_texto'], height=200)

# --- MÓDULO 2: VIDEOS CORTOS ---
st.divider()
st.header("🎬 Módulo 2: Video TikTok")
guion_largo = st.text_area("Guion podcast:", height=100, key="video")
if st.button("Extraer Guion 60s"):
    model = buscar_mejor_modelo()
    res = model.generate_content(f"Resume a 60s (gancho, desarrollo, CTA). Solo texto de lectura: {guion_largo}")
    st.session_state['guion_tiktok'] = res.text

if 'guion_tiktok' in st.session_state:
    guion_final = st.text_area("Edita tu guion:", value=st.session_state['guion_tiktok'], height=150)
    if st.button("🎙️ Generar Audio"):
        resultado = generar_audio(guion_final, "tiktok_catolico.mp3")
        if resultado["success"]:
            st.audio(resultado["ruta"])
            with open(resultado["ruta"], "rb") as f:
                st.download_button("⬇️ Descargar MP3", f, file_name="tiktok_catolico.mp3")

# --- MÓDULO 3: INSTAGRAM (CARRUSEL PARA CANVA) ---
st.divider()
st.header("🎨 Módulo 3: Carrusel para Canva")
tema_carrusel = st.text_area("Tema para el carrusel:", height=80, key="carrusel")
if st.button("Diseñar Carrusel"):
    model = buscar_mejor_modelo()
    res = model.generate_content(f"Crea 5 diapositivas para Instagram sobre: {tema_carrusel}. Devuelve solo los 5 textos enumerados.")
    st.session_state['carrusel_texto'] = res.text

if 'carrusel_texto' in st.session_state:
    textos = st.session_state['carrusel_texto'].split('\n')
    df = pd.DataFrame({"Texto_Diapositiva": [t for t in textos if t.strip()]})
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Descargar CSV para Canva (Bulk Create)", csv, "carrusel.csv", "text/csv")
