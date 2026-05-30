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
