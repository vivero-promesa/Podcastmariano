import os
import asyncio
import re
import edge_tts

def generar_audio(texto_guion, nombre_archivo="capsula_audio.mp3"):
    print("🎙️ Limpiando guion e iniciando Edge-TTS...")
    
    # 1. LIMPIEZA DE TEXTO (Vital para evitar que el motor falle)
    # Esto borra todo lo que esté entre corchetes [MÚSICA...] y los asteriscos **
    texto_limpio = re.sub(r'\[.*?\]', '', texto_guion)
    texto_limpio = texto_limpio.replace('*', '').strip()
    
    if not texto_limpio:
        return {"success": False, "error": "El texto quedó vacío tras la limpieza."}

    # 2. Voz Oficial
    VOICE = "es-CO-SalomeNeural" 
    
    ruta_absoluta = os.path.abspath(nombre_archivo)
    
    # 3. Instanciamos la comunicación (Sin RATE por ahora para asegurar compatibilidad)
    async def construir_audio():
        communicate = edge_tts.Communicate(texto_limpio, VOICE)
        await communicate.save(ruta_absoluta)

    try:
        asyncio.run(construir_audio())
        print(f"✅ Audio generado con éxito en: {ruta_absoluta}")
        return {"success": True, "ruta": ruta_absoluta}
        
    except Exception as e:
        print(f"❌ Error al procesar audio: {str(e)}")
        return {"success": False, "error": f"Error con Edge-TTS: {str(e)}"}
