"""Estudio de producción — La maternidad no siempre tiene cuna; a veces tiene cruz.

Flujo semanal: Documento(s) → Enfoque → Investigación (texto oficial) → Censor → tu aprobación →
Guion → Censor del guion → tu aprobación → Paquete de publicación → Historial (+ voz IA opcional).
"""
import hashlib
import io
import json
import os
import tempfile
import zipfile
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import config
from agents import historial as hist
from agents import borrador
from agents.enfoques import proponer_enfoques, puntos_tratados
from agents.investigator import investigar
from agents.narrador import generar_audio
from agents.novedades import DDF_DESDE, buscar_documentos_nuevos
from agents.publicacion import crear_paquete, descripcion_spotify, hashtags_tiktok_finales
from agents.script_writer import escribir_guion
from agents.theologian import resumen_para_correccion, revisar
from paginas.comun import casilla_aprobacion, exigir_clave, mostrar_revision

CLAVES = ["inv", "rev_inv", "ok_inv", "guion", "rev_guion", "ok_guion", "paquete", "voz", "guardado"]
MAX_DOCUMENTOS = 3


EDITOR_GUION = "editor_guion"  # clave del cuadro de texto editable del guion


def reiniciar(desde: str = "inv"):
    borrar = CLAVES[CLAVES.index(desde):]
    for k in borrar:
        st.session_state.pop(k, None)
    if "guion" in borrar:
        st.session_state.pop(EDITOR_GUION, None)


def poner_guion(texto: str):
    """Guion nuevo o corregido: lo guarda y lo pone en el cuadro editable (que antes conservaba el texto viejo)."""
    st.session_state.guion = texto
    st.session_state[EDITOR_GUION] = texto


def huella(texto: str) -> str:
    return hashlib.sha1((texto or "").encode("utf-8")).hexdigest()


for k in ("inv", "rev_inv", "guion", "rev_guion", "paquete", "voz", "guardado", "enfoques", "novedades"):
    st.session_state.setdefault(k, None)


def recargar_historial():
    st.session_state.historial, _ = hist.cargar()


if st.session_state.get("historial") is None:
    recargar_historial()


def guardar_historial(mensaje: str) -> bool:
    """Guarda en GitHub. Sin token, ofrece el archivo para subirlo a mano."""
    if not hist.puede_guardar():
        st.warning(
            "Falta GITHUB_TOKEN en los Secrets de Streamlit, así que no puedo guardar en GitHub. "
            f"Descarga el archivo y súbelo al repositorio con el nombre {hist.ARCHIVO}."
        )
        st.download_button(
            f"⬇️ Descargar {hist.ARCHIVO}", hist.a_json(st.session_state.historial).encode("utf-8"),
            file_name=hist.ARCHIVO, mime="application/json", key=f"dl_hist_{mensaje}",
        )
        return False
    try:
        enlace = hist.guardar(st.session_state.historial, mensaje)
        st.success("Guardado en GitHub." + (f" [Ver el cambio]({enlace})" if enlace else ""))
        return True
    except Exception as e:
        st.error(f"No pude guardar en GitHub: {e}")
        return False


st.title("🎙️ Estudio de producción")
st.caption("Del documento de la Iglesia al episodio listo para grabar y publicar el viernes.")
exigir_clave()

# ─────────────────────────── Recuperar trabajo guardado ───────────────────────────
st.session_state.setdefault("duracion", 18)
if "_borrador" not in st.session_state:
    st.session_state._borrador = borrador.cargar()
_b = st.session_state._borrador
if _b and not st.session_state.get("inv") and not st.session_state.get("enfoques"):
    with st.container(border=True):
        st.info(f"💾 Tienes trabajo guardado ({_b.get('fecha', '')}): **{_b.get('resumen', '')}**")
        r1, r2 = st.columns(2)
        r1.button("↩️ Recuperar mi trabajo", type="primary", on_click=borrador.restaurar, args=(st.session_state, _b))
        if r2.button("🗑️ Descartarlo y empezar de cero"):
            borrador.borrar()
            st.session_state._borrador = None
            st.rerun()

if st.button("🔄 Empezar episodio nuevo"):
    reiniciar()
    st.session_state.enfoques = None
    borrador.borrar()
    st.session_state._borrador = None
    st.session_state.pop("_borrador_huella", None)
    st.rerun()


def correr_investigacion(tema, documentos, indicaciones, correcciones="", informe_anterior=""):
    """Investiga (o corrige) y revisa, mostrando cada paso."""
    titulo = "Aplicando las correcciones del Censor…" if correcciones else "Investigando…"
    with st.status(titulo, expanded=True) as estado:
        oficiales = [d for d in documentos if d.get("url")]
        if oficiales:
            nombres = ", ".join(d["titulo"] for d in oficiales)
            st.write(f"📖 Leyendo el texto oficial en vatican.va: {nombres}…")
        if not oficiales:
            st.write("🌐 Buscando fuentes en la web (sin texto oficial)…")
        st.write("🔎 Redactando el informe con citas exactas…" if not correcciones else "🛠️ Reescribiendo el informe con las correcciones…")
        inv = investigar(tema, indicaciones=indicaciones, correcciones=correcciones,
                         informe_anterior=informe_anterior, documentos=documentos)
        st.write("⛪ El Censor Doctrinal está verificando cada cita contra su documento…")
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
    poner_guion(guion)
    st.session_state.rev_guion = rev


historial = st.session_state.historial
catalogo = hist.catalogo(historial)
por_clave = {d["clave"]: d for d in catalogo}

# ─────────────────────────── Documentos nuevos del Papa ───────────────────────────
with st.expander("🆕 Buscar documentos nuevos del Papa y de la Santa Sede"):
    st.caption(
        "Revisa en vatican.va las encíclicas, exhortaciones, cartas apostólicas y motu proprio de León XIV "
        f"y los documentos del Dicasterio para la Doctrina de la Fe desde {DDF_DESDE}. "
        "Solo muestra los que tratan la vida, la familia o la bioética y aún no están en el catálogo."
    )
    if st.button("🔍 Buscar documentos nuevos"):
        with st.spinner("Revisando vatican.va…"):
            try:
                st.session_state.novedades = buscar_documentos_nuevos(historial)
            except Exception as e:
                st.session_state.novedades = {"nuevos": [], "descartados": [], "errores": [str(e)], "revisados": 0}
    nov = st.session_state.novedades
    if nov:
        for err in nov["errores"]:
            st.warning(f"No pude revisar {err}")
        if not nov["nuevos"] and nov["revisados"]:
            st.info(f"Revisé {nov['revisados']} documentos: no hay nada nuevo relacionado con el podcast.")
        for i, c in enumerate(nov["nuevos"]):
            ya = hist._url_normal(c.url) in hist.urls_conocidas(historial)
            st.markdown(f"**{c.titulo_corto}** ({c.anio}) · {c.tipo} — {c.tema}  \n{c.por_que}  \n[Abrir en vatican.va]({c.url})")
            if ya:
                st.caption("✅ Ya está en el catálogo.")
            elif st.button("➕ Agregar al catálogo", key=f"agregar_{i}"):
                recargar_historial()
                try:
                    doc = hist.agregar_documento(st.session_state.historial, c.titulo_corto, c.anio, c.tema, c.url)
                    if guardar_historial(f"Catálogo: agrega {doc['titulo']}"):
                        st.rerun()
                except ValueError as e:
                    st.info(str(e))
        if nov["descartados"]:
            st.caption(
                f"Revisados sin relación con el podcast ({len(nov['descartados'])}): "
                + " · ".join(f"[{c.titulo_corto}]({c.url})" for c in nov["descartados"])
            )

# ─────────────────────────── 1. Documento(s) y enfoque ───────────────────────────
st.header("1. Documento(s) y enfoque")

tratadas = hist.claves_tratadas(historial)
if "docs_sel" in st.session_state:
    st.session_state.docs_sel = [c for c in st.session_state.docs_sel if c in por_clave]
else:
    pendiente = next((d["clave"] for d in catalogo if d["clave"] not in tratadas), catalogo[0]["clave"])
    st.session_state.docs_sel = [pendiente]


def al_cambiar_documentos():
    st.session_state.enfoques = None
    sel = [por_clave[c] for c in st.session_state.docs_sel if c in por_clave]
    st.session_state.tema_input = sel[0]["tema"] if len(sel) == 1 else ""


def etiqueta(clave: str) -> str:
    d = por_clave[clave]
    n = len(hist.episodios_de(historial, clave))
    return config.etiqueta_documento(d) + (f" · {n} episodio(s)" if n else " · nuevo")


st.multiselect(
    f"Documento(s) de la semana (hasta {MAX_DOCUMENTOS})",
    [d["clave"] for d in catalogo], key="docs_sel", format_func=etiqueta,
    max_selections=MAX_DOCUMENTOS, on_change=al_cambiar_documentos,
    help="Combina 2 o 3 documentos para mostrar cómo evolucionó la enseñanza "
         "(ej.: Donum Vitae + Dignitas Personae). Sin documento = tema libre con búsqueda web.",
)
documentos = [por_clave[c] for c in st.session_state.docs_sel if c in por_clave]
if "tema_input" not in st.session_state:
    st.session_state.tema_input = documentos[0]["tema"] if len(documentos) == 1 else ""

ya_tratado = hist.resumen_tratado(historial, documentos)
if ya_tratado:
    with st.expander("📚 Lo que ya se trató de estos documentos"):
        st.markdown(ya_tratado)

if st.button("💡 Proponer enfoques nuevos"):
    with st.spinner("Buscando enfoques que no se hayan tratado…"):
        st.session_state.enfoques = proponer_enfoques(documentos, historial)


def usar_enfoque(pregunta: str):
    st.session_state.tema_input = pregunta


if st.session_state.enfoques:
    for i, e in enumerate(st.session_state.enfoques):
        with st.container(border=True):
            st.markdown(f"**{e.pregunta}**  \n{e.por_que}")
            st.caption("Profundiza: " + " · ".join(e.puntos))
            st.button("Usar este enfoque", key=f"enfoque_{i}", on_click=usar_enfoque, args=(e.pregunta,))

c1, c2 = st.columns([2, 1])
with c1:
    tema = st.text_input(
        "Pregunta o enfoque del episodio",
        key="tema_input",
        help="Escríbelo como lo buscaría la gente. Ej.: «¿La FIV es pecado? Lo que dice la Iglesia»",
    )
with c2:
    duracion = st.slider("Duración (minutos)", 8, 25, key="duracion")
indic_inv = st.text_area("Indicaciones para la investigación (opcional)", height=90)

indicaciones = indic_inv
if ya_tratado:
    indicaciones = (indic_inv + "\n\n" if indic_inv else "") + (
        "YA SE TRATÓ EN EPISODIOS ANTERIORES (no lo repitas; profundiza lo nuevo):\n" + ya_tratado
    )

if st.button("🔎 Investigar y revisar", type="primary", disabled=not tema.strip()):
    reiniciar()
    correr_investigacion(tema, documentos, indicaciones)

# ─────────────────────────── 2. Investigación ───────────────────────────
if st.session_state.inv:
    inv, rev_inv = st.session_state.inv, st.session_state.rev_inv
    st.header("2. Investigación")
    if inv["con_fuente_oficial"]:
        st.success(f"Basada en el texto oficial: {inv['fuente_url']}")
    else:
        st.warning(
            ("Falta el texto oficial de algún documento: sus citas van marcadas con [VERIFICAR]." if inv["fuente_texto"]
             else "Sin texto oficial (se usó búsqueda web). Revisa las citas marcadas con [VERIFICAR].")
            + (f" Detalle: {inv['error_fuente']}" if inv["error_fuente"] else "")
        )
    with st.expander("Ver informe de investigación"):
        st.markdown(inv["informe"])
    mostrar_revision(rev_inv, "Censor (investigación)")

    if rev_inv.veredicto != "APROBADO":
        if st.button("🛠️ Aplicar las correcciones del Censor a la investigación", type="primary"):
            correr_investigacion(
                tema, documentos, indicaciones,
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
        # El cuadro tiene clave propia: muestra siempre el último guion (también el corregido por el
        # Censor) y todo lo que escribas en él es lo que usan el paquete, el .zip y la voz IA.
        if st.session_state.get(EDITOR_GUION) is None:
            st.session_state[EDITOR_GUION] = st.session_state.guion
        st.text_area("Guion (editable: tu palabra es la final)", key=EDITOR_GUION, height=420)
        st.session_state.guion = st.session_state[EDITOR_GUION]
        if rev_g.veredicto == "RECHAZADO":
            st.error("Guion rechazado por el Censor. Aplica las correcciones antes de seguir.")
        casilla_aprobacion(rev_g, "Apruebo el guion para grabar (Directora)", "ok_guion")

# ─────────────────────────── 4. Publicación ───────────────────────────
if st.session_state.get("ok_guion") and st.session_state.guion:
    st.header("4. Paquete de publicación")
    nombre_docs = " + ".join(config.etiqueta_documento(d) for d in documentos) or "Tema libre"
    if st.button("📦 Crear títulos, descripción y hashtags", type="primary"):
        with st.status("Preparando el paquete…", expanded=True) as estado:
            st.write("🔤 Títulos con las palabras que la gente busca…")
            st.write("📝 Descripción para Spotify con enlaces a redes…")
            st.session_state.paquete = crear_paquete(st.session_state.guion, tema, nombre_docs)
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

        st.subheader("📚 Guardar en el historial")
        st.caption(
            "Registra el episodio con su enfoque y los puntos que profundizó, para que los próximos enfoques no los repitan. "
            "Hazlo después de descargar el .zip."
        )
        if st.session_state.guardado:
            st.success(f"Episodio {st.session_state.guardado} guardado en el historial.")
        elif st.button("📚 Guardar este episodio en el historial"):
            with st.spinner("Resumiendo los puntos que se profundizaron…"):
                puntos = puntos_tratados(st.session_state.guion, tema)
            recargar_historial()
            nuevo = hist.agregar_episodio(st.session_state.historial, documentos, tema, titulo, puntos)
            st.markdown("**Puntos profundizados:**\n" + "\n".join(f"- {p}" for p in nuevo["puntos"]))
            if guardar_historial(f"Historial: episodio {nuevo['numero']} — {titulo}"):
                st.session_state.guardado = nuevo["numero"]

        st.subheader("Voz IA (opcional)")
        st.caption("Para escuchar el guion antes de grabar. El episodio se graba con tu voz.")
        guion_actual = st.session_state.guion
        voz = st.session_state.voz
        # Una lectura hecha con una versión anterior del guion no se vuelve a mostrar.
        if voz and voz.get("huella") != huella(guion_actual):
            st.session_state.voz = voz = None
            st.warning("El guion cambió después de la última lectura: genera la lectura otra vez para escuchar la versión corregida.")
        if st.button("🗣️ Generar lectura con voz IA (guion actual)"):
            with st.status("Generando la lectura del guion actual…", expanded=False):
                ruta = os.path.join(tempfile.mkdtemp(), "lectura_guion.mp3")
                voz = generar_audio(guion_actual, ruta)
                voz["huella"] = huella(guion_actual)
                voz["palabras"] = len(guion_actual.split())
                voz["hora"] = datetime.now(ZoneInfo("America/Bogota")).strftime("%I:%M %p")
                st.session_state.voz = voz
        if voz:
            if voz["success"]:
                st.caption(f"Lectura del guion actual ({voz['palabras']} palabras), generada a las {voz['hora']}.")
                st.audio(voz["ruta"])
            else:
                st.error(voz["error"])

        st.info(
            "**Siguientes pasos:** 1) Graba el episodio con tu voz. "
            "2) Súbelo a Spotify for Creators con el título y la descripción de arriba, programado para el viernes. "
            "3) Abre **Estudio de Redes** (menú de la izquierda), sube el audio y saca los 3 clips para Instagram y TikTok."
        )

# ─────────────────────────── Historial completo ───────────────────────────
st.divider()
with st.expander(f"📖 Historial de episodios ({len(historial['episodios'])})"):
    if historial["episodios"]:
        filas = [
            {
                "N.º": e.get("numero"),
                "Fecha": e.get("fecha") or "",
                "Documento(s)": " + ".join(e.get("documentos_titulos") or []) or "Tema libre",
                "Título": e.get("titulo", ""),
                "Puntos": "; ".join(e.get("puntos") or []),
            }
            for e in sorted(historial["episodios"], key=lambda x: x.get("numero") or 0, reverse=True)
        ]
        st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
    else:
        st.caption("Todavía no hay episodios en el historial.")
    st.caption(
        "Guardado en GitHub: " + ("✅ activo" if hist.puede_guardar() else "❌ falta GITHUB_TOKEN en los Secrets")
    )
    if st.button("🔄 Recargar historial"):
        recargar_historial()
        st.rerun()

# ─────────────────────────── Guardado automático ───────────────────────────
try:
    _hora = borrador.autoguardar(st.session_state)
    if _hora:
        st.caption(f"💾 Guardado automático: {_hora}. Si la página se recarga, usa «Recuperar mi trabajo».")
except Exception as _e:
    st.caption(f"⚠️ No pude hacer el guardado automático: {_e}")
