import streamlit as st
import sys
import os

# Asegura que Python encuentre los módulos del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow.podcast_flow import build_graph
from agents.narrador import generar_audio

# ─────────────────────────────────────────────
# Configuración de Página
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Podcast Mariano AI",
    page_icon="🌹",
    layout="wide"
)

st.title("🌹 Podcast Mariano AI")
st.subheader("Panel Editorial — Directora de Estudio")

# ─────────────────────────────────────────────
# Inicialización de Session State
# ─────────────────────────────────────────────
defaults = {
    "tema": None,
    "investigacion": None,
    "teologia": None,
    "guion": None,
    "aprobado_director": False,
    "audio_path": None,
    "graph_result": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─────────────────────────────────────────────
# 1️⃣ Entrada del Tema
# ─────────────────────────────────────────────
st.header("1️⃣ Definición del Misterio o Advocación")

col_input, col_btn = st.columns([3, 1])

with col_input:
    tema_input = st.text_input(
        "Escribe el tema:",
        placeholder="Ej: Apariciones de la Virgen en Fátima"
    )

with col_btn:
    st.write("")
    st.write("")
    if st.button("🚀 Iniciar Flujo Completo", type="primary"):
        if tema_input:
            # Reiniciar estado al cambiar de tema
            for key in ["investigacion", "teologia", "guion", "aprobado_director",
                        "audio_path", "graph_result"]:
                st.session_state[key] = None
            st.session_state.aprobado_director = False
            st.session_state.tema = tema_input

            with st.spinner("🤖 Ejecutando Investigador y Censor Teológico..."):
                try:
                    graph = build_graph()
                    initial_state = {
                        "topic": tema_input,
                        "research": None,
                        "research_approved": False,
                        "research_feedback": None,
                        "theology_review": None,
                        "script": None,
                        "script_approved": False,
                        "script_feedback": None,
                        "audio_path": None,
                        "current_phase": "investigacion",
                        "revision_count": 0,
                        "approved": False,
                    }

                    # Ejecutamos solo hasta 'approval' pasando approved=True
                    # para que no bloquee en input() de CLI
                    # Usamos stream para capturar el estado intermedio
                    partial_state = initial_state.copy()

                    # Corremos investigador y teólogo manualmente para la UI
                    from agents.investigator import investigador_agent
                    from agents.theologian import teologo_agent

                    partial_state = investigador_agent(partial_state)
                    partial_state = teologo_agent(partial_state)

                    st.session_state.investigacion = partial_state.get("research")
                    st.session_state.teologia = partial_state.get("theology_review")
                    st.session_state.graph_result = partial_state

                except Exception as e:
                    st.error(f"❌ Error durante la ejecución: {e}")
        else:
            st.warning("Por favor, ingresa un tema primero.")

# ─────────────────────────────────────────────
# Resultados del Flujo
# ─────────────────────────────────────────────
if st.session_state.tema:
    st.divider()
    st.info(f"📍 **Trabajando en:** {st.session_state.tema}")

    col1, col2 = st.columns(2)

    # ─────────────────────────────────────────
    # COLUMNA IZQUIERDA: Investigación + Teología
    # ─────────────────────────────────────────
    with col1:

        # 2️⃣ Investigación
        st.header("🔎 Fase de Investigación")
        if st.session_state.investigacion:
            st.success("✅ Investigación completada.")
            with st.expander("Ver Documento de Investigación"):
                st.markdown(st.session_state.investigacion)
        else:
            st.info("Pulsa '🚀 Iniciar Flujo Completo' para ejecutar.")

        # 3️⃣ Censor Teológico
        st.header("⛪ Censor Doctrinal")
        if st.session_state.teologia:
            review = st.session_state.teologia
            veredicto = review.veredicto

            if veredicto == "APROBADO":
                st.success(f"✅ Veredicto: **{veredicto}** | Rigor: {review.nivel_rigor}/10")
            elif veredicto == "CORREGIR":
                st.warning(f"⚠️ Veredicto: **{veredicto}** | Rigor: {review.nivel_rigor}/10")
            else:
                st.error(f"❌ Veredicto: **{veredicto}** | Rigor: {review.nivel_rigor}/10")

            with st.expander("Ver Reporte Teológico Completo"):
                st.markdown(f"**Catecismo:** {review.cita_catecismo}")
                st.markdown(f"**Contexto Histórico:** {review.contexto_historico}")
                st.markdown("**Observaciones:**")
                for obs in review.observaciones:
                    st.markdown(f"- {obs}")

    # ─────────────────────────────────────────
    # COLUMNA DERECHA: Guion + Audio
    # ─────────────────────────────────────────
    with col2:

        # 4️⃣ Guionista
        st.header("✍️ Redacción de Guion")

        teologia_ok = (
            st.session_state.teologia is not None
            and st.session_state.teologia.veredicto in ("APROBADO", "CORREGIR")
        )

        if teologia_ok:
            feedback_guion = st.text_area(
                "Instrucciones opcionales para el Guionista:",
                placeholder="Ej: Usa un tono más contemplativo en el cierre.",
                height=80
            )

            if st.button("✍️ Generar Guion"):
                with st.spinner("Redactando cápsula mariana..."):
                    try:
                        from agents.script_writer import guionista_agent
                        state_con_feedback = {
                            **st.session_state.graph_result,
                            "script_feedback": feedback_guion or ""
                        }
                        result = guionista_agent(state_con_feedback)
                        st.session_state.guion = result.get("script")
                    except Exception as e:
                        st.error(f"❌ Error al generar guion: {e}")

            if st.session_state.guion:
                st.success("✅ Guion generado.")
                guion_editado = st.text_area(
                    "Borrador Final (Editable — tu última palabra):",
                    value=st.session_state.guion,
                    height=250,
                    key="guion_editable"
                )
                st.session_state.guion = guion_editado  # Guarda ediciones en vivo
        else:
            if not st.session_state.investigacion:
                st.info("Esperando investigación...")
            else:
                st.error("El Censor rechazó el contenido. No se puede generar guion.")

        # 5️⃣ Guardrail Humano + Audio
        st.header("🛡️ Locución y Exportación")

        if st.session_state.guion:
            st.warning("⚠️ Requiere revisión de la Directora Editorial.")
            aprobacion = st.checkbox(
                "He revisado el guion y apruebo su paso a ElevenLabs."
            )

            if aprobacion:
                st.session_state.aprobado_director = True

                nombre_archivo = st.text_input(
                    "Nombre del archivo MP3:",
                    value=f"capsula_{st.session_state.tema[:30].replace(' ', '_')}.mp3"
                )

                if st.button("🎙️ Generar Audio (Gastar Cuota)", type="primary"):
                    with st.spinner("🎙️ Conectando con ElevenLabs..."):
                        resultado = generar_audio(
                            st.session_state.guion,
                            nombre_archivo
                        )

                    if resultado.get("success"):
                        st.session_state.audio_path = resultado["ruta"]
                        st.success(f"✅ Audio guardado en: `{resultado['ruta']}`")
                        st.audio(resultado["ruta"])
                    else:
                        st.error(f"❌ Error: {resultado.get('error')}")
            else:
                st.session_state.aprobado_director = False
