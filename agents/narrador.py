import os
import asyncio
import re
import edge_tts
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- CONFIGURACIÓN DRIVE ---
# Reemplaza el texto de abajo con el ID alfanumérico largo de tu carpeta
DRIVE_FOLDER_ID = "https://drive.google.com/drive/folders/173b7x_rPUHL7CSpw9pcMJSlKnlqPJDb-"

def subir_a_drive(ruta_local, nombre_archivo):
    print("☁️ Iniciando subida a Google Drive...")
    try:
        # Extraemos las credenciales guardadas en los Secrets de Streamlit
        credenciales_info = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(
            credenciales_info,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        
        # Conectamos de forma segura con la API de Drive
        service = build('drive', 'v3', credentials=credentials)
        
        # Configuramos los metadatos del destino
        file_metadata = {
            'name': nombre_archivo,
            'parents': [DRIVE_FOLDER_ID]
        }
        
        # Cargamos el archivo .mp3 temporal
        media = MediaFileUpload(ruta_local, mimetype='audio/mpeg', resumable=True)
        
        # Ejecutamos el envío a los servidores de Google
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id'
        ).execute()
        
        print(f"✅ Archivo respaldado en Drive con ID: {file.get('id')}")
        return True
        
    except Exception as e:
        print(f"❌ Error crítico al subir a Google Drive: {e}")
        return False


def generar_audio(texto_guion, nombre_archivo="capsula_audio.mp3"):
    print("🎙️ Limpiando guion e iniciando Edge-TTS...")
    
    # 1. LIMPIEZA PROFUNDA DE TEXTO (Regex Avanzado)
    texto_limpio = re.sub(r'\[.*?\]', '', texto_guion)
    texto_limpio = texto_limpio.replace('*', '')
    texto_limpio = re.sub(r'(?i)\bnarrador\b[:,]?\s*', '', texto_limpio).strip()
    
    if not texto_limpio:
        return {"success": False, "error": "El texto quedó vacío tras la limpieza."}

    # 2. Voz Oficial (Acento Colombiano)
    VOICE = "es-CO-SalomeNeural" 
    ruta_absoluta = os.path.abspath(nombre_archivo)
    
    # 3. Generación del Audio Local
    async def construir_audio():
        communicate = edge_tts.Communicate(texto_limpio, VOICE)
        await communicate.save(ruta_absoluta)

    try:
        # Ejecuta la locución de Salomé
        asyncio.run(construir_audio())
        print(f"✅ Audio generado con éxito en: {ruta_absoluta}")
        
        # 4. SUBIDA AUTOMÁTICA (El puente con la nube)
        subida_exitosa = subir_a_drive(ruta_absoluta, nombre_archivo)
        
        if not subida_exitosa:
            return {
                "success": False, 
                "error": "El audio se generó bien, pero falló el respaldo automático en Google Drive. Verifica el ID de la carpeta o los permisos del bot."
            }
        
        return {
            "success": True, 
            "ruta": ruta_absoluta,
            "drive_backup": True
        }
        
    except Exception as e:
        print(f"❌ Error al procesar audio: {str(e)}")
        return {"success": False, "error": f"Error con Edge-TTS: {str(e)}"}
