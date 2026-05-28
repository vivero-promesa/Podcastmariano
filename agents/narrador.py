import os
import requests
from dotenv import load_dotenv

load_dotenv()

def generar_audio(texto_guion, nombre_archivo="capsula_audio.mp3"):
    api_key  = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

    if not api_key:
        return {"error": "Falta ELEVENLABS_API_KEY en .env"}

    print("🎙️ Conectando con ElevenLabs...")
    url     = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": api_key}
    data    = {
        "text": texto_guion,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            os.makedirs("output", exist_ok=True)
            ruta = os.path.join("output", nombre_archivo)
            with open(ruta, 'wb') as f:
                f.write(response.content)
            return {"success": True, "ruta": ruta}
        return {"error": f"ElevenLabs {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}
