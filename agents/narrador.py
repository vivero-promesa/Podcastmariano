import os
import asyncio
import re
import edge_tts
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def obtener_o_crear_carpeta(service):
    # El bot busca si ya creó su propia carpeta antes
    nombre_carpeta = "Audios Podcast Bot"
    query = f"name = '{nombre_carpeta}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    
    resultados = service.files().list(q=query, fields="files(id)").execute()
    archivos = resultados.get('files', [])
    
    if archivos:
        return archivos[0]['id']
    
    # Si no existe, el bot la crea en su propia raíz libre de bloqueos
    meta_carpeta = {
        'name': nombre_carpeta,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    carpeta = service.files().create(body=meta_carpeta, fields='id').execute()
    id_nueva_carpeta = carpeta.get('id')
    
    # IMPORTANTE: El bot te comparte LA CARPETA COMPLETA a tu correo personal automáticamente
    # REEMPLAZA EL CORREO DE ABAJO CON TU CORREO PERSONAL DE GOOGLE
    tu_correo_personal = "bot-podcast@gen-lang-client-0464943288.iam.gserviceaccount.com"
    
    permiso = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': tu_correo_personal
    }
    service.permissions().create(fileId=id_nueva_carpeta, body=permiso).execute()
    print(f"📁 Carpeta nueva creada y compartida con {tu_correo_personal}")
    
    return id_nueva_carpeta

def subir_a_drive(ruta_local, nombre_archivo):
    print("☁️ Iniciando subida a Google Drive de forma independiente...")
    try:
        credenciales_info = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(
            credenciales_info,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        
        service = build('drive', 'v3', credentials=credentials)
        
        # Obtenemos el ID de la carpeta autónoma del bot
        folder_id = obtener_o_crear_carpeta(service)
        
        file_metadata = {
            'name': nombre_archivo,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(ruta_local, mimetype='audio/mpeg', resumable=True)
        
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id'
        ).execute()
        
        print(f"✅ Archivo respaldado con éxito. ID: {file.get('id')}")
        return True
        
    except Exception as e:
        print(f"❌ Error crítico en subida: {e}")
        return False

def generar_audio(texto_guion, nombre_archivo="capsula_audio.mp3"):
    print("🎙️ Limpiando guion...")
    texto_limpio = re.sub(r'\[.*?\]', '', texto_guion)
    texto_limpio = texto_limpio.replace('*', '')
    texto_limpio = re.sub(r'(?i)\bnarrador\b[:,]?\s*', '', texto_limpio).strip()
    
    if not texto_limpio:
        return {"success": False, "error": "El texto quedó vacío tras la limpieza."}

    VOICE = "es-CO-SalomeNeural" 
    ruta_absolute = os.path.abspath(nombre_archivo)
    
    async def construir_audio():
        communicate = edge_tts.Communicate(texto_limpio, VOICE)
        await communicate.save(ruta_absolute)

    try:
        asyncio.run(construir_audio())
        
        subida_exitosa = subir_a_drive(ruta_absolute, nombre_archivo)
        
        if not subida_exitosa:
            return {"success": False, "error": "Falló el guardado. El bot autónomo no pudo escribir en su espacio. Revisa logs."}
        
        return {"success": True, "ruta": ruta_absolute, "drive_backup": True}
        
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}
