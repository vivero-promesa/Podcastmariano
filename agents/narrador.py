import os
import asyncio
import re
import traceback
import edge_tts
import streamlit as st

def generar_audio(texto_guion, nombre_archivo="capsula_audio.mp3"):
    # 1. Filtros nuevos: Eliminar frases no deseadas
    texto_limpio = texto_guion.replace('--- PREGUNTA CENTRAL ---', '')
    texto_limpio = texto_limpio.replace('--- CONFLICTO ---', '')
    
    # 2. Filtros anteriores: Limpiar corchetes, asteriscos y la palabra "Narrador:"
    texto_limpio = re.sub(r'\[.*?\]', '', texto_limpio)
    texto_limpio = texto_limpio.replace('*', '')
    texto_limpio = re.sub(r'(?i)\bnarrador\b[:,]?\s*', '', texto_limpio).strip()
    
    if not texto_limpio:
        return {"success": False, "error": "Texto vacío tras limpieza."}

    VOICE = "es-CO-SalomeNeural" 
    ruta_absolute = os.path.abspath(nombre_archivo)
    
    async def construir_audio():
        # Fijamos la velocidad normal (+0%). 
        # Si la sientes lenta, puedes poner "+10%", si la sientes rápida "-10%"
        communicate = edge_tts.Communicate(texto_limpio, VOICE, rate="+0%")
        await communicate.save(ruta_absolute)

    try:
        # Generamos el audio directamente en el servidor
        asyncio.run(construir_audio())
        
        # Devolvemos la ruta local para que Streamlit lo reproduzca
        return {"success": True, "ruta": ruta_absolute, "drive_backup": False}
        
    except Exception as e:
        return {"success": False, "error": f"Error al generar voz: {str(e)}"}
