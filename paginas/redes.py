"""Estudio de Redes: clips virales desde el episodio grabado, títulos para el buscador,
carruseles para Canva y cápsulas con voz IA."""
import io
import os
import tempfile
import zipfile

import pandas as pd
import streamlit as st

import config
from agents import llm, video
from agents.carrusel import crear_carrusel
from agents.clips import a_segundos, analizar_episodio, producir_clip, textos_clip
from agents.narrador import generar_audio
from agents.publicacion import hashtags_instagram_finales, mejorar_titulos
from paginas.comun import exigir_clave

st.title("📱 Estudio de Redes")
st.caption("Cada clip lleva a Spotify: gancho en pantalla, subtítulos y «Episodio completo en Spotify».")

exigir_clave()
if not video.ffmpeg_disponible():
    st.warning("ffmpeg no está instalado: los videos no se pueden crear. Revisa que exista packages.txt con «ffmpeg».")

st.session_state.setdefault("trabajo", None)
st.session_state.setdefault("analisis", None)
st.session_state.setdefault("producidos", {})

tab_clips, tab_titulos, tab_carrusel, tab_capsula = st.tabs(
    ["🎬 Clips del episodio", "🔤 Títulos para el buscador", "⏸️ Carrusel (en pausa)", "⏸️ Cápsula voz IA (en pausa)"]
)

# ─────────────────────────── Clips del episodio ───────────────────────────
with tab_clips:
    st.subheader("Del episodio grabado a 3 videos verticales")
    c1, c2 = st.columns([2, 1])
    with c1:
        audio_subido = st.file_uploader("Audio del episodio", type=["mp3", "m4a", "wav", "aac", "ogg"])
        contexto = st.text_input("¿De qué trata el episodio? (opcional)", placeholder="Ej.: Humanae Vitae, anticoncepción")
        enlace_ep = st.text_input(
            "Enlace del episodio en Spotify (opcional)",
            placeholder="https://open.spotify.com/episode/…",
            help="Si lo pegas, los textos de cada clip usan el enlace de este episodio y no el del programa.",
        )
    with c2:
        cantidad = st.slider(
            "Número de clips", 1, 7, config.CLIPS_POR_SEMANA,
            help="Modelo vigente: 3 clips por semana, el mismo archivo en Instagram y TikTok.",
        )
        fondo_subido = st.file_uploader("Imagen de fondo (opcional)", type=["jpg", "jpeg", "png"])
        con_subtitulos = st.checkbox("Subtítulos automáticos", value=True)

    if st.button("🎬 Encontrar los mejores momentos", type="primary", disabled=audio_subido is None):
        carpeta = tempfile.mkdtemp(prefix="clips_")
        original = os.path.join(carpeta, "original" + os.path.splitext(audio_subido.name)[1].lower())
        with open(original, "wb") as f:
            f.write(audio_subido.getbuffer())
        episodio = os.path.join(carpeta, "episodio.mp3")
        fondo = None
        if fondo_subido:
            fondo = os.path.join(carpeta, "fondo" + os.path.splitext(fondo_subido.name)[1].lower())
            with open(fondo, "wb") as f:
                f.write(fondo_subido.getbuffer())
        with st.status("Analizando el episodio…", expanded=True) as estado:
            st.write("🎧 Preparando el audio…")
            video.normalizar_audio(original, episodio)
            minutos = video.duracion_segundos(episodio) / 60
            st.write(f"⬆️ Enviando {minutos:.0f} minutos de audio a Gemini…")
            st.write("🔎 Escuchando el episodio completo y eligiendo los mejores momentos (30-90 segundos)…")
            st.session_state.analisis = analizar_episodio(episodio, cantidad, contexto)
            estado.update(label=f"{len(st.session_state.analisis.clips)} momentos encontrados", state="complete", expanded=False)
        st.session_state.trabajo = {"carpeta": carpeta, "episodio": episodio, "fondo": fondo}
        st.session_state.producidos = {}

    analisis = st.session_state.analisis
    trabajo = st.session_state.trabajo
    if analisis and trabajo:
        st.markdown("#### Capítulos para la descripción de Spotify")
        st.code("\n".join(analisis.capitulos), language=None)

        if st.button("⚙️ Crear todos los videos"):
            barra = st.progress(0.0, text="Preparando…")
            for i, clip in enumerate(analisis.clips):
                barra.progress(i / len(analisis.clips), text=f"Clip {i + 1} de {len(analisis.clips)}: cortando, subtitulando y armando el video…")
                try:
                    st.session_state.producidos[i] = producir_clip(
                        trabajo["episodio"], a_segundos(clip.inicio), a_segundos(clip.fin), clip.gancho,
                        trabajo["carpeta"], f"clip_{i + 1}", trabajo["fondo"], con_subtitulos,
                    )
                except Exception as e:
                    st.session_state.producidos[i] = {"error": str(e)}
            barra.progress(1.0, text="Videos listos")

        for i, clip in enumerate(analisis.clips):
            with st.expander(f"Clip {i + 1} · {clip.inicio}–{clip.fin} · {clip.gancho}", expanded=i == 0):
                st.caption(f"Por qué funciona: {clip.por_que_funciona}")

                # ── ✂️ Editar el clip ──
                st.markdown("**✂️ Editar el clip**")
                a, b, c = st.columns([1, 1, 2])
                ini = a.text_input("Inicio (MM:SS)", value=clip.inicio, key=f"ini_{i}")
                fin = b.text_input("Fin (MM:SS)", value=clip.fin, key=f"fin_{i}")
                gancho = c.text_input("Gancho en pantalla", value=clip.gancho, key=f"gan_{i}")
                d1, d2 = st.columns(2)
                antes = d1.number_input(
                    "Empezar antes (segundos)", 0, 30, 0, key=f"antes_{i}",
                    help="Si el clip arranca con una frase cortada, súmale segundos al inicio.",
                )
                despues = d2.number_input(
                    "Terminar después (segundos)", 0, 30, 0, key=f"despues_{i}",
                    help="Si la idea queda a medias, súmale segundos al final.",
                )
                t_ini = max(0.0, a_segundos(ini) - antes)
                t_fin = a_segundos(fin) + despues
                st.caption(f"Duración del clip: {t_fin - t_ini:.0f} segundos (ideal entre 30 y 90).")

                # ── 🖼️ Imagen ──
                st.markdown("**🖼️ Imagen de fondo**")
                g1, g2 = st.columns([2, 1])
                img_clip = g1.file_uploader(
                    "Cambiar la imagen de este clip (opcional)", type=["jpg", "jpeg", "png"], key=f"img_{i}"
                )
                ajuste = g2.radio(
                    "Cómo se ve la imagen", ["Completa (sin recortar)", "Llenar la pantalla"], key=f"ajuste_{i}",
                    help="«Completa» muestra toda la foto con un fondo difuminado; «Llenar» la amplía y recorta los bordes.",
                )
                fondo_clip = trabajo["fondo"]
                if img_clip is not None:
                    fondo_clip = os.path.join(trabajo["carpeta"], f"fondo_clip_{i + 1}" + os.path.splitext(img_clip.name)[1].lower())
                    with open(fondo_clip, "wb") as f:
                        f.write(img_clip.getbuffer())
                    g1.image(img_clip, width=120)

                e1, e2 = st.columns(2)
                if e1.button("▶️ Escuchar el tramo", key=f"oir_{i}"):
                    try:
                        prueba = os.path.join(trabajo["carpeta"], f"prueba_{i + 1}.mp3")
                        video.cortar_audio(trabajo["episodio"], t_ini, t_fin, prueba)
                        st.audio(prueba)
                    except Exception as e:
                        st.error(str(e))
                if e2.button("🎞️ Crear / rehacer este video", key=f"hacer_{i}", type="primary"):
                    with st.spinner("Cortando, subtitulando y armando el video…"):
                        try:
                            st.session_state.producidos[i] = producir_clip(
                                trabajo["episodio"], t_ini, t_fin, gancho,
                                trabajo["carpeta"], f"clip_{i + 1}", fondo_clip, con_subtitulos,
                                ajuste="llenar" if ajuste == "Llenar la pantalla" else "completa",
                            )
                        except Exception as e:
                            st.session_state.producidos[i] = {"error": str(e)}

                hecho = st.session_state.producidos.get(i)
                if hecho and hecho.get("error"):
                    st.error(hecho["error"])
                elif hecho:
                    st.divider()
                    v1, v2 = st.columns([1, 2])
                    with v1:
                        st.video(hecho["mp4"])
                        with open(hecho["mp4"], "rb") as f:
                            st.download_button("⬇️ Descargar video MP4", f.read(), file_name=f"clip_{i + 1}.mp4", key=f"dl_{i}")
                    with v2:
                        textos = textos_clip(clip, enlace_ep)
                        st.text_area("Instagram (Reel)", value=textos["instagram"], height=170, key=f"ig_{i}")
                        st.markdown("**📤 TikTok** — copia el texto con el ícono de la esquina:")
                        st.code(textos["tiktok"], language=None)
                        st.link_button("📤 Publicar en TikTok", "https://www.tiktok.com/tiktokstudio/upload", type="primary")
                        st.caption(
                            "1) Descarga el MP4 · 2) Pulsa «Publicar en TikTok» (se abre TikTok Studio) · "
                            "3) Sube el video y pega el texto copiado. "
                            f"Enlace del episodio en la bio → {textos['enlace']}. "
                            "En Instagram, si tu cuenta tiene la opción, compártelo como Reel de prueba (Trial Reel)."
                        )

        listos = {i: d for i, d in st.session_state.producidos.items() if d and not d.get("error")}
        if listos:
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as z:
                for i, d in listos.items():
                    z.write(d["mp4"], f"clip_{i + 1}.mp4")
                    if d.get("srt"):
                        z.write(d["srt"], f"clip_{i + 1}.srt")
                    t = textos_clip(analisis.clips[i], enlace_ep)
                    z.writestr(f"clip_{i + 1}_textos.txt", f"INSTAGRAM\n{t['instagram']}\n\nTIKTOK\n{t['tiktok']}\n")
                z.writestr("capitulos_spotify.txt", "\n".join(analisis.capitulos))
            st.download_button("⬇️ Descargar todos los clips (.zip)", buffer.getvalue(), file_name="clips.zip", mime="application/zip")

# ─────────────────────────── Títulos para el buscador ───────────────────────────
with tab_titulos:
    st.subheader("Renombra los episodios ya publicados")
    st.caption("Spotify te encuentra por búsqueda: los títulos deben usar las palabras que la gente escribe.")
    actuales = st.text_area("Títulos actuales (uno por línea)", height=220)
    if st.button("🔤 Proponer títulos nuevos", disabled=not actuales.strip()):
        lista = [t.strip() for t in actuales.splitlines() if t.strip()]
        with st.spinner("Reescribiendo títulos…"):
            nuevos = mejorar_titulos(lista)
        st.dataframe(pd.DataFrame({"Antes": lista, "Después": (nuevos + [""] * len(lista))[: len(lista)]}), width="stretch")

# ─────────────────────────── Carrusel ───────────────────────────
with tab_carrusel:
    st.info("En pausa en el modelo vigente: no se publica carrusel cada semana. Úsalo solo si tú lo decides.")
    st.subheader("Carrusel de Instagram para Canva")
    tema_carrusel = st.text_input("Tema del carrusel", placeholder="Ej.: 5 cosas que dice la Iglesia sobre la FIV")
    n_diap = st.slider("Diapositivas", 5, 10, 7)
    if st.button("🎨 Crear carrusel", disabled=not tema_carrusel.strip()):
        with st.spinner("Diseñando el carrusel…"):
            st.session_state.carrusel = crear_carrusel(tema_carrusel, n_diap)
    car = st.session_state.get("carrusel")
    if car:
        df = pd.DataFrame([{"Titulo": d.titulo, "Texto": d.texto} for d in car.diapositivas])
        st.dataframe(df, width="stretch")
        st.download_button("⬇️ CSV para Canva (Bulk Create)", df.to_csv(index=False).encode("utf-8"), "carrusel.csv", "text/csv")
        st.text_area("Caption", value=car.caption + "\n\n" + " ".join(hashtags_instagram_finales(car.hashtags)), height=180)

# ─────────────────────────── Cápsula con voz IA ───────────────────────────
with tab_capsula:
    st.info("En pausa en el modelo vigente: el episodio se graba con tu voz. Úsalo solo si tú lo decides.")
    st.subheader("Cápsula de 60 segundos sin grabar")
    st.caption("Convierte un guion o una idea en un video vertical con voz IA y subtítulos.")
    base = st.text_area("Guion o idea", height=150)
    gancho_capsula = st.text_input("Gancho en pantalla", placeholder="¿La FIV es pecado?")
    if st.button("🗣️ Crear cápsula", disabled=not base.strip()):
        with st.status("Creando la cápsula…", expanded=True) as estado:
            st.write("✍️ Escribiendo el guion de 60 segundos…")
            guion60 = llm.texto(
                "Resume en un guion hablado de 60 segundos (máximo 150 palabras): gancho en la primera frase, "
                "una idea central fiel a la doctrina católica dicha con ternura, y cierre «Escucha el episodio "
                f"completo en Spotify, enlace en la bio». Solo el texto que se lee.\n\n{base}",
                temperatura=0.6,
            )
            st.write("🗣️ Locutando con voz IA…")
            carpeta = tempfile.mkdtemp(prefix="capsula_")
            voz = generar_audio(guion60, os.path.join(carpeta, "voz.mp3"))
            if not voz["success"]:
                st.error(voz["error"])
            else:
                st.write("🎞️ Subtitulando y armando el video…")
                try:
                    hecho = producir_clip(
                        voz["ruta"], 0, video.duracion_segundos(voz["ruta"]),
                        gancho_capsula or "Lo que nadie te contó", carpeta, "capsula",
                    )
                    st.session_state.capsula = {"guion": guion60, **hecho}
                    estado.update(label="Cápsula lista", state="complete", expanded=False)
                except Exception as e:
                    st.error(str(e))
    cap = st.session_state.get("capsula")
    if cap:
        st.text_area("Guion leído", value=cap["guion"], height=150)
        st.video(cap["mp4"])
        with open(cap["mp4"], "rb") as f:
            st.download_button("⬇️ Video MP4", f.read(), file_name="capsula.mp4")
