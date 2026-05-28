import os
import asyncio
import edge_tts

def generar_audio(texto_guion, nombre_archivo="capsula_audio.mp3"):
    print("🎙️ Iniciando generación de audio gratuita con Edge-TTS (Acento Local)...")
    
    # EL NOMBRE OFICIAL CORRECTO PARA COLOMBIA ES SALOMÉ
    VOICE = "es-CO-SalomeNeural" 
    
    # Mantenemos el ritmo pausado
    RATE = "-8%"
    
    ruta_absoluta = os.path.abspath(nombre_archivo)
    
    async def construir_audio():
        communicate = edge_tts.Communicate(texto_guion, VOICE, rate=RATE)
        await communicate.save(ruta_absoluta)

    try:
        asyncio.run(construir_audio())
        print(f"✅ Audio generado con éxito en: {ruta_absoluta}")
        return {"success": True, "ruta": ruta_absoluta}
        
    except Exception as e:
        print(f"❌ Error al procesar audio: {str(e)}")
        return {"success": False, "error": f"Error con Edge-TTS: {str(e)}"}
