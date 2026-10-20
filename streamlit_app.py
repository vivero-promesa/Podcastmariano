"""Punto de entrada: menú de páginas y barra lateral común.

Ejecutar con:  streamlit run streamlit_app.py
"""
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config  # noqa: E402
from paginas.comun import barra_lateral  # noqa: E402

st.set_page_config(page_title=config.PODCAST["nombre_corto"], page_icon="🎙️", layout="wide")

navegacion = st.navigation(
    [
        st.Page("paginas/produccion.py", title="Estudio de producción", icon="🎙️", default=True),
        st.Page("paginas/redes.py", title="Estudio de Redes", icon="📱"),
    ]
)
barra_lateral()
navegacion.run()
