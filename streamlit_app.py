"""Estudio de producción — La maternidad no siempre tiene cuna.

Flujo semanal: Documento → Investigación (texto oficial) → Censor → tu aprobación →
Guion → Censor del guion → tu aprobación → Paquete de publicación (+ voz IA opcional).
"""
import io
import json
import os
import sys
import tempfile
import zipfile

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config  # noqa: E402
from agents import video  # noqa: E402
from agents.investigator import investigar  # noqa: E402
from agents.narrador import generar_audio  # noqa: E402
from agents.publicacion import crear_paquete, descripcion_spotify, hashtags_tiktok_finales  # noqa: E402
from agents.script_writer import escribir_guion  # noqa: E402
from agents.theologian import resumen_para_correccion, revisar  # noqa: E402

st.set_page_config(page_title="Estudio del podcast", page_icon="🎙️", layout="wide")

P = config.PODCAST
CLAVES = ["inv", "rev_inv", "inv_ok", "guion", "rev_guion", "guion_ok", "paquete", "voz"]


def reiniciar(desde: int = 0):
    for k in CLAVES[desde:]:
        st.session_state[k] = None


for k in CLAVES:
    st.session_state.setdefault(k, None)


def mostrar_revision(rev, titulo: str):
    color = {"APROBADO": st.success, "CORREGIR": st.warning}.get(rev.veredicto, st.error)
    color(f"{titulo}: **{rev.veredicto}** · Rigor {rev.nivel_rigor}/10")
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


# ─────────────────────────── Barra lateral ───────────────────────────
with st.sidebar:
    st.markdown(f"### 🎙️ {P['nombre_corto']}")
    st.caption(P["descripcion"])
    st.markdown(f"[Spotify]({P['spotify']}) · [Instagram]({P['instagram_url']}) · [TikTok]({P['tiktok_url']})")
    st.divider()
    st.markdown("**Estado de conexiones**")
    st.write(("✅" if config.api_key() else "❌") + " Clave de Gemini")
    st.write(("✅" if video.ffmpeg_disponible() else "❌") + " ffmpeg (clips de video)")
    st.caption(f"Modelo: {config.MODELO}")
    if st.button("🔄 Empezar episodio nuevo"):
        reiniciar()
        st.rerun()

st.title("🎙️ Estudio de producción")
st.caption("Del documento de la Iglesia al episodio listo para grabar y publicar el viernes.")

if not config.api_key():
    st.error("Falta la clave GOOGLE_API_KEY. Agrégala en los Secrets de Streamlit o en el archivo .env.")
    st.stop()

# ─────────────────────────── 1. Documento y tema ───────────────────────────
st.header("1. Documento y tema")
opciones = config.DOCUMENTOS + [config.TEMA_LIBRE]
c1, c2 = st.columns([2, 1])
with c1:
    documento = st.selectbox("Documento de la semana", opciones, format_func=config.etiqueta_documento)
    tema = st.text_input(
        "Pregunta o enfoque del episodio",
        value=documento["tema"],
        help="Escríbelo como lo buscaría la gente. Ej.: «¿La FIV es pecado? Lo que dice la Iglesia»",
    )
with c2:
    duracion = st.slider("Duración (minutos)", 8, 25, 18)
    indic_inv = st.text_area("Indicaciones para la investigación (opcional)", height=90)

if st.button("🔎 Investigar y revisar", type="primary", disabled=not tema.strip()):
    reiniciar()
    with st.spinner("Leyendo el documento oficial e investigando…"):
        st.session_state.inv = investigar(tema, documento if documento["url"] else None, indic_inv)
    with st.spinner("El Censor Doctrinal está revisando la investigación…"):
        st.session_state.rev_inv = revisar(
            st.session_state.inv["informe"], "investigación", st.session_state.inv["fuente_texto"]
        )

# ─────────────────────────── 2. Investigación ───────────────────────────
if st.session_state.inv:
    inv = st.session_state.inv
    st.header("2. Investigación")
    if inv["con_fuente_oficial"]:
        st.success(f"Basada en el texto oficial: {inv['fuente_url']}")
    else:
        st.warning(
            "Sin texto oficial (se usó búsqueda web). Revisa las citas marcadas con [VERIFICAR]."
            + (f" Detalle: {inv['error_fuente']}" if inv["error_fuente"] else "")
        )
    with st.expander("Ver informe de investigación", expanded=False):
        st.markdown(inv["informe"])
    mostrar_revision(st.session_state.rev_inv, "Censor (investigación)")

    if st.session_state.rev_inv.veredicto == "RECHAZADO":
        st.error("El Censor rechazó la investigación. Ajusta el enfoque o las indicaciones e investiga de nuevo.")
    else:
        st.session_state.inv_ok = st.checkbox("✅ Apruebo la investigación (Directora)", value=bool(st.session_state.inv_ok))

# ─────────────────────────── 3. Guion ───────────────────────────
if st.session_state.inv_ok:
    st.header("3. Guion")
    indic_guion = st.text_area("Indicaciones para el guion (opcional)", placeholder="Ej.: abre con la historia de una pareja que esperó 8 años.")
    if st.button("✍️ Escribir guion y revisarlo", type="primary"):
        reiniciar(3)
        with st.spinner("Escribiendo el guion…"):
            st.session_state.guion = escribir_guion(st.session_state.inv["informe"], tema, duracion, indic_guion)
        with st.spinner("El Censor está revisando el guion final…"):
            st.session_state.rev_guion = revisar(st.session_state.guion, "guion", st.session_state.inv["fuente_texto"])

    if st.session_state.guion:
        mostrar_revision(st.session_state.rev_guion, "Censor (guion final)")
        if st.session_state.rev_guion.veredicto != "APROBADO":
            if st.button("🛠️ Aplicar las correcciones del Censor"):
                with st.spinner("Corrigiendo y volviendo a revisar…"):
                    st.session_state.guion = escribir_guion(
                        st.session_state.inv["informe"], tema, duracion, indic_guion,
                        correcciones=resumen_para_correccion(st.session_state.rev_guion),
                        guion_anterior=st.session_state.guion,
                    )
                    st.session_state.rev_guion = revisar(st.session_state.guion, "guion", st.session_state.inv["fuente_texto"])
                st.rerun()

        palabras = len(st.session_state.guion.split())
        st.caption(f"{palabras} palabras ≈ {palabras // 140} minutos. Las partes entre [CLIP] y [/CLIP] son los momentos para redes.")
        st.session_state.guion = st.text_area("Guion (editable: tu palabra es la final)", value=st.session_state.guion, height=420)

        if st.session_state.rev_guion.veredicto == "RECHAZADO":
            st.error("Guion rechazado por el Censor. Aplica las correcciones o reescríbelo.")
        else:
            st.session_state.guion_ok = st.checkbox("✅ Apruebo el guion para grabar (Directora)", value=bool(st.session_state.guion_ok))

# ─────────────────────────── 4. Publicación ───────────────────────────
if st.session_state.guion_ok:
    st.header("4. Paquete de publicación")
    if st.button("📦 Crear títulos, descripción y hashtags", type="primary"):
        with st.spinner("Preparando el paquete para Spotify y redes…"):
            st.session_state.paquete = crear_paquete(st.session_state.guion, tema, config.etiqueta_documento(documento))

    paq = st.session_state.paquete
    if paq:
        titulo = st.radio("Título del episodio (pensado para el buscador)", paq.titulos)
        desc = descripcion_spotify(paq)
        st.text_area("Descripción para Spotify (copiar y pegar)", value=desc, height=260)
        st.caption("Cuando tengas el audio, el Estudio de Redes te da los capítulos con minutos para agregarlos aquí.")
        c1, c2 = st.columns(2)
        c1.markdown("**Instagram:** " + " ".join(paq.hashtags_instagram))
        c2.markdown("**TikTok:** " + " ".join(hashtags_tiktok_finales(paq.hashtags_tiktok)))
        st.markdown(f"**Texto de portada:** {paq.texto_portada}")
        st.code(paq.prompt_portada, language=None)

        # Descarga de todo el episodio
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as z:
            z.writestr("guion.md", st.session_state.guion)
            z.writestr("investigacion.md", st.session_state.inv["informe"])
            z.writestr("publicacion.md", f"# {titulo}\n\n{desc}\n\nPortada: {paq.texto_portada}\n\nPrompt portada:\n{paq.prompt_portada}\n")
            z.writestr("revision_censor.json", json.dumps({
                "investigacion": st.session_state.rev_inv.model_dump(),
                "guion": st.session_state.rev_guion.model_dump(),
            }, ensure_ascii=False, indent=2))
        st.download_button("⬇️ Descargar episodio (.zip)", buffer.getvalue(), file_name="episodio.zip", mime="application/zip")

        st.subheader("Voz IA (opcional)")
        st.caption("Para escuchar el guion antes de grabar. El episodio se graba con tu voz.")
        if st.button("🗣️ Generar lectura con voz IA"):
            with st.spinner("Generando audio…"):
                ruta = os.path.join(tempfile.mkdtemp(), "lectura_guion.mp3")
                st.session_state.voz = generar_audio(st.session_state.guion, ruta)
        if st.session_state.voz:
            if st.session_state.voz["success"]:
                st.audio(st.session_state.voz["ruta"])
            else:
                st.error(st.session_state.voz["error"])

        st.info(
            "**Siguientes pasos:** 1) Graba el episodio con tu voz. "
            "2) Súbelo a Spotify for Creators con el título y la descripción de arriba, programado para el viernes. "
            "3) Abre **Estudio Redes** (menú de la izquierda), sube el audio y saca los clips para TikTok e Instagram."
        )
