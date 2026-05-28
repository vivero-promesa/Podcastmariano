import os
import asyncio
import re
import edge_tts

def generar_audio(texto_guion, nombre_archivo="capsula_audio.mp3"):
    print("🎙️ Limpiando guion e iniciando Edge-TTS...")
    
    # 1. LIMPIEZA PROFUNDA DE TEXTO (Regex Avanzado)
    # A. Borra todo lo que esté entre corchetes [MÚSICA...]
    texto_limpio = re.sub(r'\[.*?\]', '', texto_guion)
    
    # B. Borra los asteriscos de negritas de Markdown
    texto_limpio = texto_limpio.replace('*', '')
    
    # C. NUEVO: Fulmina la palabra "Narrador", "narrador:", "Narrador," al inicio de las frases
    # (?i) hace que no importe si está en mayúsculas o minúsculas
    # \b asegura que sea la palabra exacta
    # [:,]? elimina si hay comas o dos puntos pegados
    texto_limpio = re.sub(r'(?i)\bnarrador\b[:,]?\s*', '', texto_limpio)
    
    # D. Quita espacios vacíos al principio y al final
    texto_limpio = texto_limpio.strip()
    
    if not texto_limpio:
        return {"success": False, "error": "El texto quedó vacío tras la limpieza."}

    # 2. Voz Oficial (Acento Colombiano)
    VOICE = "es-CO-SalomeNeural" 
    
    ruta_absoluta = os.path.abspath(nombre_archivo)
    
    # 3. Instanciamos la comunicación (Sin rate para evitar bloqueos)
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
