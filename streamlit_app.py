"""Punto de entrada: menú de páginas y barra lateral común.

Ejecutar con:  streamlit run streamlit_app.py
"""
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config  # noqa: E402
from agents.llm import GeminiOcupado  # noqa: E402
from paginas.comun import barra_lateral  # noqa: E402

st.set_page_config(page_title=config.PODCAST["nombre_corto"], page_icon="🎙️", layout="wide")

navegacion = st.navigation(
    [
        st.Page("paginas/produccion.py", title="Estudio de producción", icon="🎙️", default=True),
        st.Page("paginas/redes.py", title="Estudio de Redes", icon="📱"),
    ]
)
barra_lateral()
try:
    navegacion.run()
except GeminiOcupado as e:
    # Saturación temporal de Google: aviso amable en vez de la pantalla roja de error.
    st.warning(str(e), icon="⏳")
    st.caption("Tus archivos siguen cargados: solo vuelve a pulsar el mismo botón en unos minutos.")
