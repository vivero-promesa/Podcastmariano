import streamlit as st
import google.generativeai as genai

# Configuración
st.set_page_config(page_title="Estudio de Redes", page_icon="📱", layout="wide")
st.title("📱 Estudio de Redes y Distribución")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Falta la llave de Gemini en los Secrets.")

# --- CAMBIO INTELIGENTE: BUSCAR MODELO AUTOMÁTICAMENTE ---
def get_model():
    # Esta función busca modelos que soporten generación de contenido
    models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # Filtramos para buscar un modelo estable (preferimos los que contienen 'gemini')
    for m in models:
        if 'gemini' in m.name:
            return genai.GenerativeModel(m.name)
    return None

st.divider()

# --- MÓDULO 1 ---
st.header("📦 Módulo 1: Kit de Lanzamiento")
tema_podcast = st.text_area("Tema del episodio:", height=100)

if st.button("Generar Kit de Episodio"):
    model = get_model()
    if model:
        try:
            prompt = f"Actúa como experto en Teología Católica. Crea un kit para: {tema_podcast}. Incluye: 3 títulos, descripción y 10 hashtags. Reglas: Tono reverente, fiel al Magisterio, cero terminología protestante."
            respuesta = model.generate_content(prompt)
            st.session_state['kit_generado'] = respuesta.text
        except Exception as e:
            st.error(f"Error al conectar: {e}")
    else:
        st.error("No se encontró ningún modelo de Gemini disponible en tu cuenta. Revisa tu cuenta en AI Studio.")

if 'kit_generado' in st.session_state:
    st.text_area("Resultado:", value=st.session_state['kit_generado'], height=350)
