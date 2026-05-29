import os
import asyncio
import re
import traceback
import edge_tts
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def subir_a_drive_raiz(ruta_local, nombre_archivo):
    print("☁️ Intentando subida forzada a la raíz del bot...")
    try:
        credenciales_info = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(
            credenciales_info,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        service = build('drive', 'v3', credentials=credentials)
        
        # Subimos directamente a la raíz del bot, sin carpetas externas
        file_metadata = {'name': f"PRUEBA_DEBUG_{nombre_archivo}"}
        media = MediaFileUpload(ruta_local, mimetype='audio/mpeg', resumable=True)
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return True
        
    except Exception as e:
        # Extraemos la traza completa y cruda del error
        return traceback.format_exc()

def generar_audio(texto_guion, nombre_archivo="capsula_audio.mp3"):
    texto_limpio = re.sub(r'\[.*?\]', '', texto_guion)
    texto_limpio = texto_limpio.replace('*', '')
    texto_limpio = re.sub(r'(?i)\bnarrador\b[:,]?\s*', '', texto_limpio).strip()
    
    if not texto_limpio:
        return {"success": False, "error": "Texto vacío tras limpieza."}

    VOICE = "es-CO-SalomeNeural" 
    ruta_absolute = os.path.abspath(nombre_archivo)
    
    async def construir_audio():
        communicate = edge_tts.Communicate(texto_limpio, VOICE)
        await communicate.save(ruta_absolute)

    try:
        asyncio.run(construir_audio())
        
        # Ejecutamos la subida forzada
        resultado_subida = subir_a_drive_raiz(ruta_absolute, nombre_archivo)
        
        if resultado_subida is not True:
            # Si no devuelve True, devuelve el log crudo. Lo imprimimos en pantalla.
            return {"success": False, "error": f"💥 DIAGNÓSTICO CRUDO DE GOOGLE:\n\n{resultado_subida}"}
            
        return {"success": True, "ruta": ruta_absolute, "drive_backup": True}
        
    except Exception as e:
        return {"success": False, "error": f"Error general: {str(e)}"}
