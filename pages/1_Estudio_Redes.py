import streamlit as st
import google.generativeai as genai

# 1. Configuración de la página anexa
st.set_page_config(page_title="Estudio de Redes", page_icon="📱", layout="wide")
st.title("📱 Estudio de Redes y Distribución")
st.markdown("Genera contenido derivado de tu podcast para redes sociales bajo una estricta visión católica.")

# 2. Conexión segura con tu llave de Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Falta la llave de Gemini en los Secrets. Verifica la configuración de Streamlit.")

st.divider()

# --- MÓDULO 1: KIT DE LANZAMIENTO ---
st.header("📦 Módulo 1: Kit de Lanzamiento (Spotify / YouTube)")

# Entrada del usuario
tema_podcast = st.text_area("¿De qué trata el episodio que acabas de grabar?", height=100, 
                            placeholder="Ej: La importancia del rezo del Santo Rosario en familia y sus promesas...")

if st.button("Generar Kit de Episodio"):
    if tema_podcast:
        with st.spinner("Generando propuestas fieles al Magisterio..."):
            try:
                # Usamos el modelo rápido y económico
                model = genai.GenerativeModel('gemini-1.5-flash') 
                
                # EL BLINDAJE CATÓLICO (System Prompt)
                prompt = f"""
                Actúa como un experto en Teología Católica fiel al Magisterio de la Iglesia y como un especialista en marketing digital católico.
                
                Tarea: Crea un kit de lanzamiento para un episodio de podcast sobre el siguiente tema: "{tema_podcast}".
                
                El kit debe contener exactamente:
                1. 3 opciones de título (1 intrigante, 1 formativo, 1 inspiracional).
                2. Una descripción persuasiva de 1 párrafo para animar a la escucha.
                3. Una lista de 10 hashtags optimizados para SEO (mezclando nicho católico y crecimiento espiritual general).
                
                REGLAS ESTRICTAS:
                - Cero terminología protestante o de nueva era.
                - Tono reverente, formativo y directo.
                - Formato limpio para copiar y pegar fácilmente.
                """
                
                respuesta = model.generate_content(prompt)
                
                # Guardamos la respuesta en la "memoria" temporal para no perderla al editar
                st.session_state['kit_generado'] = respuesta.text
                
            except Exception as e:
                st.error(f"Error al conectar con Gemini: {str(e)}")
    else:
        st.warning("Por favor, escribe un pequeño resumen del tema primero para que la IA tenga contexto.")

# 3. Interfaz de Edición Manual (Cero Gasto de Tokens)
if 'kit_generado' in st.session_state:
    st.subheader("📝 Edita y Aprueba tu Kit")
    st.markdown("Borra, corrige o ajusta las opciones aquí mismo. **Lo que escribas en esta caja no consume tokens.**")
    
    # La caja de texto editable
    texto_final = st.text_area("Resultado Final:", value=st.session_state['kit_generado'], height=350)
    st.divider()

# --- MÓDULO 2: VIDEOS CORTOS (TIKTOK / REELS) ---
st.header("🎬 Módulo 2: Adaptación a Video Corto (TikTok / Reels)")
st.markdown("Transforma tu guion principal en una cápsula de 60 segundos, lista para ser narrada y publicada.")

guion_original = st.text_area("Pega aquí el guion completo de tu podcast:", height=150, key="input_guion_video")

if st.button("Extraer Guion de 60 Segundos"):
    if guion_original:
        with st.spinner("Adaptando el guion con fidelidad doctrinal..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # EL BLINDAJE CATÓLICO PARA VIDEO
                prompt_video = f"""
                Actúa como un experto en Teología Católica y un creador de contenido digital formativo.
                
                Tarea: Resume el siguiente guion de podcast para crear un guion de video vertical (TikTok/Reels) de máximo 60 segundos (aproximadamente 130-150 palabras).
                
                Estructura obligatoria:
                1. GANCHO: Una frase inicial (primeros 3 segundos) que atrape la atención sin caer en sensacionalismo.
                2. DESARROLLO: El núcleo del mensaje teológico, claro y directo.
                3. LLAMADO A LA ACCIÓN (CTA): Una breve invitación final a escuchar el episodio completo del podcast.
                
                REGLAS ESTRICTAS:
                - Fidelidad absoluta al Magisterio de la Iglesia Católica.
                - Cero terminología protestante o de nueva era.
                - Tono reverente, formativo y dinámico.
                - Escribe SOLO el texto que el narrador va a leer (sin acotaciones visuales, corchetes, ni títulos), para que pueda ser procesado limpiamente por el motor de voz.
                
                Guion original:
                {guion_original}
                """
                
                respuesta_video = model.generate_content(prompt_video)
                st.session_state['guion_corto_generado'] = respuesta_video.text
                
            except Exception as e:
                st.error(f"Error al conectar con Gemini: {str(e)}")
    else:
        st.warning("Por favor, pega el guion de tu podcast primero.")

# Interfaz de Edición Manual
if 'guion_corto_generado' in st.session_state:
    st.subheader("📝 Edita tu Guion Corto")
    st.markdown("Ajusta las palabras para que suene natural al hablar. **Edición sin costo de tokens.**")
    
    texto_video_final = st.text_area("Guion Final para Video:", value=st.session_state['guion_corto_generado'], height=250, key="edit_guion_video")
