"""Elementos compartidos por todas las páginas."""
import streamlit as st

import config
from agents import video

P = config.PODCAST


def barra_lateral():
    """Nombre del podcast, enlaces y estado de conexiones, visible en todas las páginas."""
    with st.sidebar:
        st.markdown(f"### 🎙️ {P['nombre_corto']}")
        st.caption(P["descripcion"])
        st.markdown(f"[Spotify]({P['spotify']}) · [Instagram]({P['instagram_url']}) · [TikTok]({P['tiktok_url']})")
        st.divider()
        st.markdown("**Estado de conexiones**")
        st.write(("✅" if config.api_key() else "❌") + " Clave de Gemini")
        st.write(("✅" if video.ffmpeg_disponible() else "❌") + " ffmpeg (clips de video)")
        st.caption(f"Modelo: {config.MODELO}")


def exigir_clave():
    if not config.api_key():
        st.error("Falta la clave GOOGLE_API_KEY. Agrégala en los Secrets de Streamlit o en el archivo .env.")
        st.stop()


def mostrar_revision(rev, titulo: str):
    aviso = {"APROBADO": st.success, "CORREGIR": st.warning}.get(rev.veredicto, st.error)
    aviso(f"{titulo}: **{rev.veredicto}** · Rigor {rev.nivel_rigor}/10")
    with st.expander("Ver revisión completa del Censor"):
        if rev.citas_verificadas:
            st.markdown("**Citas verificadas**\n" + "\n".join(f"- {c}" for c in rev.citas_verificadas))
        if rev.citas_dudosas:
            st.markdown("**Citas dudosas**\n" + "\n".join(f"- {c}" for c in rev.citas_dudosas))
        if rev.afirmaciones_a_corregir:
            st.markdown("**A corregir**\n" + "\n".join(f"- {c}" for c in rev.afirmaciones_a_corregir))
        st.markdown(f"**Tono pastoral:** {rev.tono_pastoral}")
        if rev.observaciones:
            st.markdown("**Observaciones**\n" + "\n".join(f"- {c}" for c in rev.observaciones))


def casilla_aprobacion(rev, etiqueta: str, clave: str) -> bool:
    """Aprobación de la Directora.

    APROBADO → casilla normal. CORREGIR → solo se puede aprobar marcando que es bajo su criterio.
    RECHAZADO → no se puede aprobar.
    """
    if rev.veredicto == "RECHAZADO":
        return False
    if rev.veredicto == "APROBADO":
        return st.checkbox(f"✅ {etiqueta}", key=clave)
    st.caption("El Censor pidió correcciones. Lo recomendado es aplicarlas antes de aprobar.")
    return st.checkbox(f"⚠️ {etiqueta} aunque el Censor pidió corregir (bajo mi criterio)", key=clave)
