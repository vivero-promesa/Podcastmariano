import os
import requests
import streamlit as st

def generar_audio(texto_guion, nombre_archivo="capsula_audio.mp3"):
    print("🎙️ Iniciando módulo de audio...")
    
    # 1. MODO SEGURO STREAMLIT: Buscar la llave nativamente en los Secretos de la nube
    try:
        api_key = st.secrets["ELEVENLABS_API_KEY"]
    except Exception:
        # Fallback por si alguna vez vuelves a correrlo en tu computadora
        api_key = os.getenv("ELEVENLABS_API_KEY")
        
    voice_id = "EXAVITQu4vr4xnSDxMaL"  # El ID de tu narrador

    if not api_key:
        return {"error": "No se encontró ELEVENLABS_API_KEY en los secretos."}

    print("🎙️ Conectando con los servidores de ElevenLabs...")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg", 
        "Content-Type": "application/json", 
        "xi-api-key": api_key
    }
    
    data = {
        "text": texto_guion,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # 2. RUTAS SEGURAS: Forzamos una ruta absoluta temporal sin subcarpetas conflictivas
            ruta_absoluta = os.path.abspath(nombre_archivo)
            
            with open(ruta_absoluta, 'wb') as f:
                f.write(response.content)
                
            return {"success": True, "ruta": ruta_absoluta}
        else:
            return {"error": f"Error de ElevenLabs ({response.status_code}): {response.text}"}
            
    except Exception as e:
        return {"error": f"Error interno al guardar: {str(e)}"}
