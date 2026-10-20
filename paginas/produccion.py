"""Estudio de producción — La maternidad no siempre tiene cuna.

Flujo semanal: Documento → Investigación (texto oficial) → Censor → tu aprobación →
Guion → Censor del guion → tu aprobación → Paquete de publicación (+ voz IA opcional).
"""
import io
import json
import os
import tempfile
import zipfile

import streamlit as st

import config
from agents.investigator import investigar
from agents.narrador import generar_audio
from agents.publicacion import crear_paquete, descripcion_spotify, hashtags_tiktok_finales
from agents.script_writer import escribir_guion
from agents.theologian import resumen_para_correccion, revisar
from paginas.comun import casilla_aprobacion, exigir_clave, mostrar_revision

CLAVES = ["inv", "rev_inv", "ok_inv", "guion", "rev_guion", "ok_guion", "paquete", "voz"]


def reiniciar(desde: str = "inv"):
    for k in CLAVES[CLAVES.index(desde):]:
        st.session_state.pop(k, None)


for k in ("inv", "rev_inv", "guion", "rev_guion", "paquete", "voz"):
    st.session_state.setdefault(k, None)

st.title("🎙️ Estudio de producción")
st.caption("Del documento de la Iglesia al episodio listo para grabar y publicar el viernes.")
exigir_clave()

if st.button("🔄 Empezar episodio nuevo"):
    reiniciar()
    st.rerun()


def correr_investigacion(tema, documento, indicaciones, correcciones="", informe_anterior=""):
    """Investiga (o corrige) y revisa, mostrando cada paso."""
    titulo = "Aplicando las correcciones del Censor…" if correcciones else "Investigando…"
    with st.status(titulo, expanded=True) as estado:
        if documento and documento.get("url"):
            st.write(f"📖 Leyendo el texto oficial de {documento['titulo']} en vatican.va…")
        else:
            st.write("🌐 Buscando fuentes en la web (sin documento oficial)…")
        st.write("🔎 Redactando el informe con citas exactas…" if not correcciones else "🛠️ Reescribiendo el informe con las correcciones…")
        inv = investigar(tema, documento, indicaciones, correcciones, informe_anterior)
        st.write("⛪ El Censor Doctrinal está verificando cada cita contra el documento…")
        rev = revisar(inv["informe"], "investigación", inv["fuente_texto"])
        estado.update(label=f"Investigación lista · Censor: {rev.veredicto}", state="complete", expanded=False)
    reiniciar("ok_inv")
    st.session_state.inv, st.session_state.rev_inv = inv, rev


def correr_guion(tema, duracion, indicaciones, correcciones="", guion_anterior=None):
    titulo = "Aplicando las correcciones del Censor al guion…" if correcciones else "Escribiendo el guion…"
    with st.status(titulo, expanded=True) as estado:
        st.write("✍️ Escribiendo con la fórmula de retención y los 5 momentos [CLIP]…" if not correcciones else "🛠️ Reescribiendo el guion con las correcciones…")
        guion = escribir_guion(
            st.session_state.inv["informe"], tema, duracion, indicaciones,
            correcciones=correcciones, guion_anterior=guion_anterior,
        )
        st.write("⛪ El Censor Doctrinal está revisando el guion final…")
        rev = revisar(guion, "guion", st.session_state.inv["fuente_texto"])
        estado.update(label=f"Guion listo · Censor: {rev.veredicto}", state="complete", expanded=False)
    reiniciar("ok_guion")
    st.session_state.guion, st.session_state.rev_guion = guion, rev


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

doc_base = documento if documento["url"] else None

if st.button("🔎 Investigar y revisar", type="primary", disabled=not tema.strip()):
    reiniciar()
    correr_investigacion(tema, doc_base, indic_inv)

# ─────────────────────────── 2. Investigación ───────────────────────────
if st.session_state.inv:
    inv, rev_inv = st.session_state.inv, st.session_state.rev_inv
    st.header("2. Investigación")
    if inv["con_fuente_oficial"]:
        st.success(f"Basada en el texto oficial: {inv['fuente_url']}")
    else:
        st.warning(
            "Sin texto oficial (se usó búsqueda web). Revisa las citas marcadas con [VERIFICAR]."
            + (f" Detalle: {inv['error_fuente']}" if inv["error_fuente"] else "")
        )
    with st.expander("Ver informe de investigación"):
        st.markdown(inv["informe"])
    mostrar_revision(rev_inv, "Censor (investigación)")

    if rev_inv.veredicto != "APROBADO":
        if st.button("🛠️ Aplicar las correcciones del Censor a la investigación", type="primary"):
            correr_investigacion(
                tema, doc_base, indic_inv,
                correcciones=resumen_para_correccion(rev_inv), informe_anterior=inv["informe"],
            )
            st.rerun()
    if rev_inv.veredicto == "RECHAZADO":
        st.error("El Censor rechazó la investigación. Aplica las correcciones o cambia el enfoque.")
    casilla_aprobacion(rev_inv, "Apruebo la investigación (Directora)", "ok_inv")

# ─────────────────────────── 3. Guion ───────────────────────────
if st.session_state.get("ok_inv") and st.session_state.inv:
    st.header("3. Guion")
    indic_guion = st.text_area(
        "Indicaciones para el guion (opcional)",
        placeholder="Ej.: abre con la historia de una pareja que esperó 8 años.",
    )
    if st.button("✍️ Escribir guion y revisarlo", type="primary"):
        reiniciar("guion")
        correr_guion(tema, duracion, indic_guion)

    if st.session_state.guion:
        rev_g = st.session_state.rev_guion
        mostrar_revision(rev_g, "Censor (guion final)")
        if rev_g.veredicto != "APROBADO":
            if st.button("🛠️ Aplicar las correcciones del Censor al guion", type="primary"):
                correr_guion(
                    tema, duracion, indic_guion,
                    correcciones=resumen_para_correccion(rev_g), guion_anterior=st.session_state.guion,
                )
                st.rerun()

        palabras = len(st.session_state.guion.split())
        st.caption(f"{palabras} palabras ≈ {palabras // 140} minutos. Las partes entre [CLIP] y [/CLIP] son los momentos para redes.")
        st.session_state.guion = st.text_area(
            "Guion (editable: tu palabra es la final)", value=st.session_state.guion, height=420
        )
        if rev_g.veredicto == "RECHAZADO":
            st.error("Guion rechazado por el Censor. Aplica las correcciones antes de seguir.")
        casilla_aprobacion(rev_g, "Apruebo el guion para grabar (Directora)", "ok_guion")

# ─────────────────────────── 4. Publicación ───────────────────────────
if st.session_state.get("ok_guion") and st.session_state.guion:
    st.header("4. Paquete de publicación")
    if st.button("📦 Crear títulos, descripción y hashtags", type="primary"):
        with st.status("Preparando el paquete…", expanded=True) as estado:
            st.write("🔤 Títulos con las palabras que la gente busca…")
            st.write("📝 Descripción para Spotify con enlaces a redes…")
            st.session_state.paquete = crear_paquete(st.session_state.guion, tema, config.etiqueta_documento(documento))
            estado.update(label="Paquete listo", state="complete", expanded=False)

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
            with st.status("Generando la lectura…", expanded=False):
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
            "3) Abre **Estudio de Redes** (menú de la izquierda), sube el audio y saca los clips para TikTok e Instagram."
        )
