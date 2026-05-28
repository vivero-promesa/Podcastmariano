import os
import asyncio
import edge_tts


def generar_audio(texto_guion, nombre_archivo="capsula_audio.mp3"):
    print("🎙️ Iniciando generación de audio gratuita con Edge-TTS (Acento Local)...")
    
    # Seleccionamos la voz nativa de Colombia (Acento sutil, fluido y familiar)
    VOICE = "es-CO-XimenaNeural" 
    
    # Bajamos la velocidad un 8% para darle un tono más pausado, reflexivo y orante
    RATE = "-8%"
    
    # Ruta absoluta segura dentro del servidor temporal de Streamlit Cloud
    ruta_absoluta = os.path.abspath(nombre_archivo)
    
    # Función asíncrona requerida por la librería edge-tts
    async def construir_audio():
        # Pasamos el parámetro 'rate' para controlar la velocidad de la locución
        communicate = edge_tts.Communicate(texto_guion, VOICE, rate=RATE)
        await communicate.save(ruta_absoluta)

    try:
        # Ejecuta de forma segura el proceso asíncrono dentro del flujo de Streamlit
        asyncio.run(construir_audio())
        print(f"✅ Audio generado con éxito en: {ruta_absoluta}")
        return {"success": True, "ruta": ruta_absoluta}
        
    except Exception as e:
        print(f"❌ Error al procesar audio: {str(e)}")
        return {"success": False, "error": f"Error con Edge-TTS: {str(e)}"}
