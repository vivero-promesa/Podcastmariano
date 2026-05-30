import os
import asyncio
import re
import traceback
import edge_tts
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def subir_a_drive(ruta_local, nombre_archivo):
    print("☁️ Intentando subida a la carpeta compartida...")
    try:
        credenciales_info = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(
            credenciales_info,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        service = build('drive', 'v3', credentials=credentials)
        
        # AQUÍ VA EL ID DE TU CARPETA DE GOOGLE DRIVE
        ID_CARPETA = "173b7x_rPUHL7CSpw9pcMJSlKnlqPJDb-"
        
        file_metadata = {
            'name': nombre_archivo,
            'parents': [ID_CARPETA]
        }
        media = MediaFileUpload(ruta_local, mimetype='audio/mpeg', resumable=True)
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return True
        
    except Exception as e:
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
        resultado_subida = subir_a_drive(ruta_absolute, nombre_archivo)
        
        if resultado_subida is not True:
            return {"success": False, "error": f"💥 DIAGNÓSTICO CRUDO DE GOOGLE:\n\n{resultado_subida}"}
            
        return {"success": True, "ruta": ruta_absolute, "drive_backup": True}
        
    except Exception as e:
        return {"success": False, "error": f"Error general: {str(e)}"}
