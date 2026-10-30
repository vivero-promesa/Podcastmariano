"""Pestaña «Planeación» del Estudio de Redes: estrategia, calendario de 12 semanas,
plan de los 3 clips, lista del viernes, métricas y banco de ideas."""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import config
from agents import historial as hist
from agents import planeacion as plan_mod

SIN_DOC = "LIBRE"


def _catalogo() -> dict:
    if st.session_state.get("historial") is None:
        st.session_state.historial, _ = hist.cargar()
    cat = hist.catalogo(st.session_state.historial) + [config.TEMA_LIBRE]
    return {d["clave"]: d for d in cat}


def _plan() -> dict:
    if st.session_state.get("plan") is None:
        st.session_state.plan = plan_mod.cargar()
    return st.session_state.plan


def _guardar(mensaje: str):
    try:
        donde = plan_mod.guardar(st.session_state.plan, mensaje)
        st.session_state.plan = plan_mod.cargar() if donde == "github" else st.session_state.plan
        if donde == "github":
            st.success("Guardado en GitHub (rama «borradores»).")
        else:
            st.warning("Guardado solo en el servidor: falta GITHUB_TOKEN. Descarga el archivo para no perderlo.")
            st.download_button("⬇️ Descargar planeacion.json", plan_mod.a_json(st.session_state.plan).encode("utf-8"),
                               file_name=plan_mod.ARCHIVO, mime="application/json")
    except Exception as e:
        st.error(f"No pude guardar el plan: {e}")


def _nombre_doc(claves, por_clave) -> str:
    nombres = [por_clave[c]["titulo"] if c in por_clave else c for c in (claves or [])]
    return " + ".join(nombres) or "Tema libre"


def _fecha_bonita(iso: str) -> str:
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    d = date.fromisoformat(iso)
    return f"{d.day} {meses[d.month - 1]} {d.year}"


def mostrar():
    por_clave = _catalogo()
    plan = _plan()

    st.subheader("🗓️ Planeación del podcast y las redes")
    st.caption(
        "Un episodio cada viernes, agrupados en series de 4. Cada semana, 3 clips (uno por pilar), "
        "el mismo archivo en Instagram, TikTok y YouTube Shorts, programados el jueves."
    )

    # ── Esta semana ──
    actual = plan_mod.semana_actual(plan)
    if actual:
        siguiente = plan_mod.siguiente_de(plan, actual)
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(
                    f"**Próximo episodio · viernes {_fecha_bonita(actual['fecha'])}**  \n"
                    f"{actual['serie']} {actual.get('parte', '')} — **{actual['enfoque'] or 'enfoque por definir'}**  \n"
                    f"Documento: {_nombre_doc(actual.get('documentos'), por_clave)}"
                    + (" · 🎤 con invitado" if actual.get("invitado") else "")
                )
                if siguiente:
                    st.caption(f"Avance para el cierre del episodio: «El próximo viernes: {siguiente['enfoque']}».")
            c2.metric("Estado", actual.get("estado", "Por producir"))
            jueves = date.fromisoformat(actual["fecha"]) - timedelta(days=1)
            st.caption(f"Programar los 3 clips: jueves {_fecha_bonita(jueves.isoformat())}.")
    else:
        st.info("El calendario no tiene semanas próximas. Agrega semanas en «Calendario».")

    t_cal, t_sem, t_vie, t_met, t_ide, t_est = st.tabs(
        ["📅 Calendario", "🎬 Plan de la semana", "✅ Lista del viernes", "📈 Métricas", "💡 Ideas", "🧭 Estrategia"]
    )

    # ── Calendario ──
    with t_cal:
        st.caption("Edita cualquier celda y pulsa Guardar. Para añadir una semana usa el botón o la última fila.")
        etiquetas = {c: f"{c} — {d['titulo']}" for c, d in por_clave.items()}
        de_etiqueta = {v: k for k, v in etiquetas.items()}
        filas = [
            {
                "Fecha": date.fromisoformat(s["fecha"]),
                "Serie": s.get("serie", ""),
                "Parte": s.get("parte", ""),
                "Documento": etiquetas.get((s.get("documentos") or [SIN_DOC])[0], etiquetas[SIN_DOC]),
                "Enfoque": s.get("enfoque", ""),
                "Invitado": bool(s.get("invitado")),
                "Estado": s.get("estado", "Por producir"),
                "Notas": s.get("notas", ""),
            }
            for s in plan["semanas"]
        ]
        editado = st.data_editor(
            pd.DataFrame(filas), hide_index=True, width="stretch", num_rows="dynamic", key="editor_calendario",
            column_config={
                "Fecha": st.column_config.DateColumn("Viernes", format="DD/MM/YYYY", required=True),
                "Serie": st.column_config.SelectboxColumn("Serie", options=plan_mod.SERIES, required=True),
                "Parte": st.column_config.TextColumn("Parte", disabled=True, help="Se calcula sola al guardar."),
                "Documento": st.column_config.SelectboxColumn("Documento", options=list(etiquetas.values())),
                "Enfoque": st.column_config.TextColumn("Enfoque (como lo busca la gente)", width="large"),
                "Invitado": st.column_config.CheckboxColumn("🎤"),
                "Estado": st.column_config.SelectboxColumn("Estado", options=plan_mod.ESTADOS, required=True),
                "Notas": st.column_config.TextColumn("Notas"),
            },
        )
        g1, g2 = st.columns(2)
        if g1.button("💾 Guardar calendario", type="primary"):
            anteriores = {s["fecha"]: s for s in plan["semanas"]}
            semanas = []
            for _, f in editado.iterrows():
                if pd.isna(f["Fecha"]):
                    continue
                fecha = pd.Timestamp(f["Fecha"]).date().isoformat()
                previa = anteriores.get(fecha, {})
                semanas.append({
                    **previa,
                    "fecha": fecha,
                    "serie": f["Serie"] or "Episodio especial",
                    "documentos": [de_etiqueta.get(f["Documento"], SIN_DOC)],
                    "enfoque": (f["Enfoque"] or "").strip(),
                    "invitado": bool(f["Invitado"]),
                    "estado": f["Estado"] or "Por producir",
                    "notas": (f["Notas"] or "").strip() if isinstance(f["Notas"], str) else "",
                })
            plan["semanas"] = semanas
            _guardar("Planeación: calendario")
            st.session_state.pop("editor_calendario", None)  # que no se repitan las filas ya guardadas
            st.rerun()
        if g2.button("➕ Agregar una semana al final"):
            plan_mod.agregar_semana(plan)
            _guardar("Planeación: semana nueva")
            st.rerun()

    # ── Plan de la semana ──
    with t_sem:
        fechas = [s["fecha"] for s in plan["semanas"]]
        if not fechas:
            st.info("Primero agrega semanas al calendario.")
        else:
            defecto = fechas.index(actual["fecha"]) if actual else 0
            elegida = st.selectbox("Semana", fechas, index=defecto, format_func=_fecha_bonita, key="semana_clips")
            semana = next(s for s in plan["semanas"] if s["fecha"] == elegida)
            st.markdown(f"**{semana['serie']} {semana.get('parte', '')} — {semana['enfoque'] or 'enfoque por definir'}**")
            st.caption("Los 3 momentos salen de los [CLIP] del guion aprobado y del Estudio de Redes (pestaña Clips).")
            clips = semana.get("clips") or [""] * len(plan_mod.PILARES)
            nuevos = []
            for i, p in enumerate(plan_mod.PILARES):
                with st.container(border=True):
                    a, b = st.columns([1, 2])
                    a.markdown(f"**Clip {p['clip']} · {p['pilar']}**  \nPublica: {p['dia']}")
                    a.caption(p["objetivo"])
                    nuevos.append(b.text_area(
                        "Momento o gancho del clip", value=clips[i] if i < len(clips) else "",
                        placeholder=f"Ejemplo: {p['ejemplo']}", key=f"clip_plan_{elegida}_{i}", height=80,
                    ))
            if st.button("💾 Guardar plan de clips", type="primary"):
                semana["clips"] = nuevos
                _guardar(f"Planeación: clips del {elegida}")

    # ── Lista del viernes ──
    with t_vie:
        if actual:
            hechos = set(plan["lista_viernes"].get(actual["fecha"], []))
            st.markdown(f"**Viernes {_fecha_bonita(actual['fecha'])}**")
            marcados = []
            for i, tarea in enumerate(plan_mod.LISTA_VIERNES):
                if st.checkbox(tarea, value=tarea in hechos, key=f"vie_{actual['fecha']}_{i}"):
                    marcados.append(tarea)
            st.progress(len(marcados) / len(plan_mod.LISTA_VIERNES), text=f"{len(marcados)} de {len(plan_mod.LISTA_VIERNES)}")
            if st.button("💾 Guardar lista", type="primary"):
                plan["lista_viernes"][actual["fecha"]] = marcados
                if len(marcados) == len(plan_mod.LISTA_VIERNES):
                    actual["estado"] = "Publicado"
                _guardar(f"Planeación: lista del {actual['fecha']}")
        else:
            st.info("No hay un viernes próximo en el calendario.")

    # ── Métricas ──
    with t_met:
        st.caption(
            "Anótalas cada lunes. Punto de partida (19 oct 2026): 0 impresiones desde Inicio, "
            "0 clics en enlaces compartidos y 0 oyentes recurrentes. Revisión completa: 19 nov 2026."
        )
        with st.form("form_metricas", clear_on_submit=True):
            m1, m2, m3 = st.columns(3)
            fecha_m = m1.date_input("Fecha", value=date.today(), format="DD/MM/YYYY")
            imp = m2.number_input("Impresiones desde Inicio (Spotify)", 0, step=1)
            clics = m3.number_input("Clics en enlaces compartidos", 0, step=1)
            m4, m5, m6, m7 = st.columns(4)
            recur = m4.number_input("Oyentes recurrentes", 0, step=1)
            repro = m5.number_input("Reproducciones (30 días)", 0, step=1)
            seg_ig = m6.number_input("Seguidores Instagram", 0, step=1)
            seg_tt = m7.number_input("Seguidores TikTok", 0, step=1)
            if st.form_submit_button("➕ Anotar métricas", type="primary"):
                plan["metricas"] = [m for m in plan["metricas"] if m["fecha"] != fecha_m.isoformat()] + [{
                    "fecha": fecha_m.isoformat(), "impresiones_inicio": imp, "clics_enlaces": clics,
                    "oyentes_recurrentes": recur, "reproducciones_30d": repro,
                    "seguidores_instagram": seg_ig, "seguidores_tiktok": seg_tt,
                }]
                plan["metricas"].sort(key=lambda m: m["fecha"])
                _guardar(f"Planeación: métricas del {fecha_m.isoformat()}")
        if plan["metricas"]:
            df = pd.DataFrame(plan["metricas"]).rename(columns={
                "fecha": "Fecha", "impresiones_inicio": "Impresiones Inicio", "clics_enlaces": "Clics enlaces",
                "oyentes_recurrentes": "Recurrentes", "reproducciones_30d": "Reproducciones 30 d",
                "seguidores_instagram": "Seguidores IG", "seguidores_tiktok": "Seguidores TikTok",
            })
            if len(df) > 1:
                st.line_chart(df.set_index("Fecha")[["Seguidores IG", "Seguidores TikTok", "Reproducciones 30 d"]])
            st.dataframe(df.sort_values("Fecha", ascending=False), hide_index=True, width="stretch")
        else:
            st.info("Todavía no hay métricas anotadas.")

    # ── Ideas ──
    with t_ide:
        st.caption("Preguntas de comentarios y mensajes: las mejores ideas para clips y episodios salen de aquí.")
        with st.form("form_idea", clear_on_submit=True):
            idea = st.text_input("Idea o pregunta", placeholder="Ej.: «¿Puedo comulgar si hice FIV?»")
            i1, i2 = st.columns(2)
            fuente = i1.selectbox("De dónde salió", ["Comentario Instagram", "Comentario TikTok", "Mensaje directo",
                                                     "Spotify", "Idea propia"])
            pilar = i2.selectbox("Pilar", [p["pilar"] for p in plan_mod.PILARES] + ["Episodio completo"])
            if st.form_submit_button("➕ Guardar idea", type="primary") and idea.strip():
                plan["ideas"].insert(0, {"fecha": date.today().isoformat(), "idea": idea.strip(),
                                         "fuente": fuente, "pilar": pilar, "usada": False})
                _guardar("Planeación: idea nueva")
        if plan["ideas"]:
            df_i = pd.DataFrame(plan["ideas"])
            editadas = st.data_editor(
                df_i, hide_index=True, width="stretch", num_rows="dynamic", key="editor_ideas",
                column_config={
                    "fecha": st.column_config.TextColumn("Fecha", disabled=True),
                    "idea": st.column_config.TextColumn("Idea", width="large"),
                    "fuente": st.column_config.TextColumn("Fuente"),
                    "pilar": st.column_config.TextColumn("Pilar"),
                    "usada": st.column_config.CheckboxColumn("Usada"),
                },
            )
            if st.button("💾 Guardar cambios en ideas"):
                plan["ideas"] = [
                    {k: (bool(v) if k == "usada" else ("" if pd.isna(v) else v)) for k, v in fila.items()}
                    for fila in editadas.to_dict("records") if str(fila.get("idea") or "").strip()
                ]
                _guardar("Planeación: ideas")
                st.session_state.pop("editor_ideas", None)
                st.rerun()
        else:
            st.info("Aún no hay ideas guardadas.")

    # ── Estrategia ──
    with t_est:
        st.markdown(
            "**Objetivo:** que las redes lleven gente al episodio de Spotify y que quien escucha vuelva el viernes "
            "siguiente.\n\n"
            "**Ritmo semanal**\n"
            "- Viernes: episodio en Spotify + clip 1.\n"
            "- Lunes: clip 2 · Miércoles: clip 3. Los 3 se programan el jueves anterior.\n"
            "- El mismo archivo va a Instagram (prioridad), TikTok y YouTube Shorts. Sin carruseles ni Historias diarias.\n\n"
            "**Los 3 pilares (un clip de cada uno por semana)**"
        )
        st.dataframe(
            pd.DataFrame([{"Clip": p["clip"], "Pilar": p["pilar"], "Día": p["dia"], "Para qué": p["objetivo"],
                           "Ejemplo": p["ejemplo"]} for p in plan_mod.PILARES]),
            hide_index=True, width="stretch",
        )
        st.markdown(
            "**Series de 4 episodios:** título con número («Antes de la FIV 2/4»), avance del siguiente al cierre "
            "y lista de reproducción en Spotify.\n\n"
            "**Ritmo mensual:** la semana 4 de cada serie lleva invitado (médico de NaProTecnología, sacerdote o "
            "pareja con testimonio). Una vez al mes, un clip que responda un comentario real.\n\n"
            "**Cuidado:** TikTok ha bloqueado cuentas provida; por eso Instagram va primero y el lenguaje acoge, "
            "no confronta."
        )
