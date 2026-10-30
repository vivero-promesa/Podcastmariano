"""Estudio de Redes: planeación (calendario, estrategia, métricas), clips virales desde el episodio grabado, títulos para el buscador,
carruseles para Canva y cápsulas con voz IA."""
import io
import os
import tempfile
import zipfile

import pandas as pd
import streamlit as st

import config
from agents import llm, video
from agents import publicar_redes as pub
from agents.carrusel import crear_carrusel
from agents.carrusel_imagenes import crear_imagenes, zip_imagenes
from agents.imagenes import generar_imagen
from agents.clips import a_segundos, analizar_episodio, producir_clip, textos_clip
from agents.narrador import generar_audio
from agents.publicacion import hashtags_instagram_finales, mejorar_titulos
from paginas.comun import exigir_clave
from paginas import planeacion_ui

st.title("📱 Estudio de Redes")
st.caption("Cada clip lleva a Spotify: gancho en pantalla, subtítulos y «Episodio completo en Spotify».")

exigir_clave()
if not video.ffmpeg_disponible():
    st.warning("ffmpeg no está instalado: los videos no se pueden crear. Revisa que exista packages.txt con «ffmpeg».")

st.session_state.setdefault("trabajo", None)
st.session_state.setdefault("analisis", None)
st.session_state.setdefault("producidos", {})
st.session_state.setdefault("fondos_ia", {})
st.session_state.setdefault("publicados", {})

tab_plan, tab_clips, tab_titulos, tab_carrusel, tab_capsula = st.tabs(
    ["🗓️ Planeación", "🎬 Clips del episodio", "🔤 Títulos para el buscador", "⏸️ Carrusel (en pausa)", "⏸️ Cápsula voz IA (en pausa)"]
)

# ─────────────────────────── Conexión con Instagram y TikTok ───────────────────────────
# Regreso de «Conectar TikTok»: TikTok vuelve a esta página con ?code=…&state=…
_qp = st.query_params
if _qp.get("code") and _qp.get("state", "").startswith("tiktok"):
    try:
        nuevo_refresh = pub.cambiar_codigo_tiktok(_qp["code"])
        st.success("✅ TikTok quedó conectado.")
        st.markdown(
            "Para que no tengas que conectarlo cada vez, copia este código y pégalo en "
            "**Settings → Secrets** de Streamlit como `TIKTOK_REFRESH_TOKEN` (dura 1 año). "
            "No lo compartas con nadie."
        )
        st.code(nuevo_refresh or "(TikTok no envió el código; vuelve a conectar)", language=None)
    except Exception as e:
        st.error(str(e))
    st.query_params.clear()


def _panel_conexiones():
    with st.expander("🔌 Conexión con Instagram y TikTok (para el botón Publicar)"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Instagram**")
            if pub.instagram_configurado():
                if st.button("Comprobar Instagram", key="prob_ig"):
                    try:
                        cta = pub.instagram_cuenta()
                        st.success(f"Conectado como @{cta['username']}")
                    except Exception as e:
                        st.error(str(e))
                if st.button("🔄 Renovar token (dura 60 días)", key="renovar_ig"):
                    try:
                        nuevo = pub.renovar_token_instagram()
                        if nuevo:
                            st.success("Token renovado. Pégalo en los Secrets como INSTAGRAM_TOKEN:")
                            st.code(nuevo, language=None)
                        else:
                            st.warning("Instagram no renovó el token. Si es un token de usuario del sistema (EAA…), no vence y no hace falta renovarlo.")
                    except Exception as e:
                        st.error(str(e))
            else:
                st.caption("Sin conectar: falta `INSTAGRAM_TOKEN` en los Secrets. Pasos en el README, sección «Publicar desde la app».")
        with c2:
            st.markdown("**TikTok**")
            if pub.tiktok_configurado():
                modo = "borrador (llega a tu bandeja de TikTok)" if config.TIKTOK_MODO != "directo" else "publicación directa"
                st.caption(f"Modo: {modo}")
                if st.button("Comprobar TikTok", key="prob_tt"):
                    try:
                        cta = pub.tiktok_cuenta()
                        st.success(f"Conectado como {cta['nombre'] or cta['usuario']}")
                    except Exception as e:
                        st.error(str(e))
            if pub.tiktok_puede_conectar():
                st.link_button("🔗 Conectar TikTok", pub.url_conectar_tiktok("tiktok"))
            elif not pub.tiktok_configurado():
                st.caption("Sin conectar: faltan `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET` y `TIKTOK_REDIRECT_URI` en los Secrets. Pasos en el README.")
        cambio = pub.refresh_tiktok_cambio()
        if cambio and cambio != config.TIKTOK_REFRESH_TOKEN and pub.tiktok_configurado():
            st.info("TikTok renovó tu código de acceso. Cuando puedas, actualiza `TIKTOK_REFRESH_TOKEN` en los Secrets con este:")
            st.code(cambio, language=None)


def _publicar(i: int, hecho: dict, texto_ig: str, texto_tt: str, en_ig: bool, en_tt: bool, prueba: bool):
    resultado = st.session_state.publicados.setdefault(i, {})
    with st.status("Publicando…", expanded=True) as estado:
        if en_ig:
            try:
                r = pub.publicar_instagram(hecho["mp4"], texto_ig, hecho.get("portada"), prueba, avisar=st.write)
                resultado["instagram"] = r
                st.write(f"✅ Instagram: publicado → {r['enlace']}")
            except Exception as e:
                resultado["instagram_error"] = str(e)
                st.error(str(e))
        if en_tt:
            try:
                r = pub.publicar_tiktok(hecho["mp4"], texto_tt, avisar=st.write)
                resultado["tiktok"] = r
                if r["modo"] == "directo":
                    st.write(f"✅ TikTok: publicado ({r['privacidad']}, estado {r['estado']})")
                else:
                    st.write("✅ TikTok: el video llegó a tu bandeja. Abre TikTok → notificaciones, pega el texto y publica.")
            except Exception as e:
                resultado["tiktok_error"] = str(e)
                st.error(str(e))
        ok = ("instagram" in resultado or not en_ig) and ("tiktok" in resultado or not en_tt)
        estado.update(label="Publicado" if ok else "Revisa los avisos", state="complete" if ok else "error")


# ─────────────────────────── Planeación ───────────────────────────
with tab_plan:
    planeacion_ui.mostrar()

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
        fondo_subido = st.file_uploader("Imagen de fondo para todos (opcional)", type=["jpg", "jpeg", "png"])
        con_subtitulos = st.checkbox("Subtítulos grandes (estilo Reels)", value=True)
        movimiento = st.checkbox(
            "Movimiento suave de la imagen", value=True,
            help="La foto se desplaza muy despacio: retiene más que una imagen quieta.",
        )

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
        st.session_state.fondos_ia = {}
        st.session_state.publicados = {}

    analisis = st.session_state.analisis
    trabajo = st.session_state.trabajo
    if analisis and trabajo:
        # Imagen general cambiada después del análisis
        if fondo_subido and not trabajo.get("fondo"):
            trabajo["fondo"] = os.path.join(trabajo["carpeta"], "fondo" + os.path.splitext(fondo_subido.name)[1].lower())
            with open(trabajo["fondo"], "wb") as f:
                f.write(fondo_subido.getbuffer())

        st.markdown("#### Capítulos para la descripción de Spotify")
        st.code("\n".join(analisis.capitulos), language=None)

        def _fondo_de(i):
            """Imagen del clip: la propia subida > la creada con IA > la general."""
            propia = st.session_state.get(f"img_{i}")
            if propia is not None:
                ruta = os.path.join(trabajo["carpeta"], f"fondo_clip_{i + 1}" + os.path.splitext(propia.name)[1].lower())
                with open(ruta, "wb") as f:
                    f.write(propia.getbuffer())
                return ruta
            return st.session_state.fondos_ia.get(i) or trabajo["fondo"]

        def _crear_imagen_ia(i, idea):
            destino = os.path.join(trabajo["carpeta"], f"ia_clip_{i + 1}.jpg")
            st.session_state.fondos_ia[i] = generar_imagen(idea, destino, "9:16")

        b1, b2 = st.columns(2)
        if b1.button("🎨 Crear imágenes con IA para todos los clips"):
            barra = st.progress(0.0, text="Pintando…")
            for i, clip in enumerate(analisis.clips):
                barra.progress(i / len(analisis.clips), text=f"Imagen {i + 1} de {len(analisis.clips)}…")
                try:
                    _crear_imagen_ia(i, st.session_state.get(f"idea_{i}") or clip.prompt_imagen or clip.gancho)
                except Exception as e:
                    st.error(f"Clip {i + 1}: {e}")
                    break
            barra.progress(1.0, text="Imágenes listas")

        if b2.button("⚙️ Crear todos los videos"):
            barra = st.progress(0.0, text="Preparando…")
            for i, clip in enumerate(analisis.clips):
                barra.progress(i / len(analisis.clips), text=f"Clip {i + 1} de {len(analisis.clips)}: cortando, subtitulando y armando el video…")
                try:
                    st.session_state.producidos[i] = producir_clip(
                        trabajo["episodio"], a_segundos(clip.inicio), a_segundos(clip.fin), clip.gancho,
                        trabajo["carpeta"], f"clip_{i + 1}", _fondo_de(i), con_subtitulos, movimiento=movimiento,
                    )
                except Exception as e:
                    st.session_state.producidos[i] = {"error": str(e)}
            barra.progress(1.0, text="Videos listos")

        _panel_conexiones()

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
                duracion = t_fin - t_ini
                aviso = "" if 30 <= duracion <= 90 else " ⚠️ fuera del rango ideal"
                st.caption(f"Duración del clip: {duracion:.0f} segundos (ideal entre 30 y 90).{aviso}")

                # ── 🖼️ Imagen ──
                st.markdown("**🖼️ Imagen de fondo**")
                g1, g2, g3 = st.columns([2, 2, 1])
                with g1:
                    idea = st.text_area(
                        "Idea de la imagen (la IA la pinta en estilo editorial católico)",
                        value=clip.prompt_imagen or clip.gancho, height=110, key=f"idea_{i}",
                    )
                    if st.button("🎨 Crear imagen con IA", key=f"ia_{i}"):
                        with st.spinner("Pintando la imagen…"):
                            try:
                                _crear_imagen_ia(i, idea)
                            except Exception as e:
                                st.error(str(e))
                with g2:
                    st.file_uploader("O sube tu propia imagen (tiene prioridad)", type=["jpg", "jpeg", "png"], key=f"img_{i}")
                    ajuste = st.radio(
                        "Cómo se ve la imagen", ["Llenar la pantalla", "Completa (sin recortar)"], key=f"ajuste_{i}",
                        help="«Llenar» amplía la foto y recorta los bordes (ideal para imágenes de la IA, ya verticales); "
                             "«Completa» muestra toda la foto con un fondo difuminado.",
                    )
                with g3:
                    actual = _fondo_de(i)
                    if actual:
                        st.image(actual, caption="Imagen actual", width=130)
                        if st.session_state.fondos_ia.get(i) and actual == st.session_state.fondos_ia[i]:
                            with open(actual, "rb") as f:
                                st.download_button("⬇️ Imagen", f.read(), file_name=f"imagen_clip_{i + 1}.jpg", key=f"dl_img_{i}")
                    else:
                        st.caption("Sin imagen: fondo morado del podcast.")

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
                                trabajo["carpeta"], f"clip_{i + 1}", _fondo_de(i), con_subtitulos,
                                ajuste="llenar" if ajuste == "Llenar la pantalla" else "completa",
                                movimiento=movimiento,
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
                        if hecho.get("portada"):
                            with open(hecho["portada"], "rb") as f:
                                st.download_button("⬇️ Portada JPG", f.read(), file_name=f"clip_{i + 1}_portada.jpg", key=f"dlp_{i}")
                    with v2:
                        textos = textos_clip(clip, enlace_ep)
                        texto_ig = st.text_area("Texto para Instagram (Reel)", value=textos["instagram"], height=170, key=f"ig_{i}")
                        texto_tt = st.text_area("Texto para TikTok", value=textos["tiktok"], height=100, key=f"tt_{i}")

                        # ── 🚀 Publicar ──
                        st.markdown("**🚀 Publicar**")
                        hay_ig, hay_tt = pub.instagram_configurado(), pub.tiktok_configurado()
                        p1, p2, p3 = st.columns(3)
                        en_ig = p1.checkbox("Instagram", value=hay_ig, disabled=not hay_ig, key=f"pub_ig_{i}")
                        en_tt = p2.checkbox("TikTok", value=hay_tt, disabled=not hay_tt, key=f"pub_tt_{i}")
                        prueba = p3.checkbox(
                            "Reel de prueba", value=False, disabled=not hay_ig, key=f"pub_prueba_{i}",
                            help="Instagram lo muestra primero a quien aún no te sigue. Si tu cuenta no lo admite, sale como Reel normal.",
                        )
                        ya = st.session_state.publicados.get(i, {})
                        repetir = True
                        if ya.get("instagram") or ya.get("tiktok"):
                            st.caption(
                                "Ya publicado: "
                                + (f"[Instagram]({ya['instagram']['enlace']}) " if ya.get("instagram") else "")
                                + ("· TikTok" if ya.get("tiktok") else "")
                            )
                            repetir = st.checkbox("Sí, quiero publicarlo otra vez", key=f"otra_{i}")
                        if hay_ig or hay_tt:
                            destinos = " y ".join(n for n, s in (("Instagram", en_ig), ("TikTok", en_tt)) if s) or "…"
                            if st.button(f"🚀 Publicar en {destinos}", key=f"pub_{i}", type="primary",
                                         disabled=not (en_ig or en_tt) or not repetir):
                                _publicar(i, hecho, texto_ig, texto_tt, en_ig, en_tt, prueba)
                        if not (hay_ig and hay_tt):
                            st.caption(
                                "Para publicar con un clic conecta las cuentas (🔌 arriba). Mientras tanto, manual: "
                                "descarga el MP4 y súbelo con estos botones, pegando el texto."
                            )
                            m1, m2 = st.columns(2)
                            if not hay_ig:
                                m1.link_button("Abrir Instagram", "https://www.instagram.com/", key=f"m_ig_{i}")
                            if not hay_tt:
                                m2.link_button("Abrir TikTok Studio", "https://www.tiktok.com/tiktokstudio/upload", key=f"m_tt_{i}")
                        st.caption(f"Enlace del episodio para la bio → {textos['enlace']}")

        listos = {i: d for i, d in st.session_state.producidos.items() if d and not d.get("error")}
        if listos:
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as z:
                for i, d in listos.items():
                    z.write(d["mp4"], f"clip_{i + 1}.mp4")
                    if d.get("srt"):
                        z.write(d["srt"], f"clip_{i + 1}.srt")
                    if d.get("portada"):
                        z.write(d["portada"], f"clip_{i + 1}_portada.jpg")
                    t = textos_clip(analisis.clips[i], enlace_ep)
                    ig = st.session_state.get(f"ig_{i}", t["instagram"])
                    tt = st.session_state.get(f"tt_{i}", t["tiktok"])
                    z.writestr(f"clip_{i + 1}_textos.txt", f"INSTAGRAM\n{ig}\n\nTIKTOK\n{tt}\n")
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
            st.session_state.carrusel_imgs = None
    car = st.session_state.get("carrusel")
    if car:
        df = pd.DataFrame([{"Titulo": d.titulo, "Texto": d.texto} for d in car.diapositivas])
        st.dataframe(df, width="stretch")
        st.download_button("⬇️ CSV para Canva (Bulk Create)", df.to_csv(index=False).encode("utf-8"), "carrusel.csv", "text/csv")
        st.text_area("Caption", value=car.caption + "\n\n" + " ".join(hashtags_instagram_finales(car.hashtags)), height=180)

        st.markdown("#### 🖼️ Imágenes listas para Instagram")
        k1, k2 = st.columns(2)
        foto_car = k1.file_uploader("Foto de fondo para el carrusel (opcional)", type=["jpg", "jpeg", "png"], key="foto_carrusel")
        with k2:
            idea_car = st.text_input("O pide la foto a la IA", value=tema_carrusel, key="idea_carrusel")
            if st.button("🎨 Crear foto de fondo con IA", key="ia_carrusel"):
                with st.spinner("Pintando la foto…"):
                    try:
                        st.session_state.foto_car_ia = generar_imagen(
                            idea_car, os.path.join(tempfile.mkdtemp(prefix="carrusel_"), "fondo_ia.jpg"), "4:5"
                        )
                    except Exception as e:
                        st.error(str(e))
            if st.session_state.get("foto_car_ia") and foto_car is None:
                st.image(st.session_state.foto_car_ia, width=120, caption="Foto de la IA")
        if st.button("🖼️ Crear imágenes del carrusel", type="primary"):
            ruta_foto = st.session_state.get("foto_car_ia")
            if foto_car is not None:
                ruta_foto = os.path.join(tempfile.mkdtemp(prefix="carrusel_"), "fondo" + os.path.splitext(foto_car.name)[1].lower())
                with open(ruta_foto, "wb") as f:
                    f.write(foto_car.getbuffer())
            with st.spinner("Dibujando las diapositivas…"):
                st.session_state.carrusel_imgs = crear_imagenes(car.diapositivas, ruta_foto)
        imgs = st.session_state.get("carrusel_imgs")
        if imgs:
            columnas = st.columns(4)
            for n, datos in enumerate(imgs):
                columnas[n % 4].image(datos, caption=f"{n + 1}/{len(imgs)}")
            texto_caption = car.caption + "\n\n" + " ".join(hashtags_instagram_finales(car.hashtags))
            st.download_button(
                "⬇️ Descargar imágenes (.zip)", zip_imagenes(imgs, texto_caption),
                file_name="carrusel.zip", mime="application/zip", type="primary",
            )
            st.caption("Formato 1080×1350 (4:5). En Instagram súbelas en orden como una sola publicación y pega el caption.")

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
