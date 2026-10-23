"""Imágenes con IA (Gemini) para los fondos de los clips y del carrusel.

Usa la misma GOOGLE_API_KEY. El modelo de imagen se elige con GEMINI_MODELO_IMAGEN
(lista separada por comas, en orden de preferencia). Si ninguno responde, la app busca
sola en tu cuenta un modelo de Gemini que genere imágenes.

Nota: en Google AI Studio la generación de imágenes puede exigir tener la facturación
activada en el proyecto de la clave; si no, Google responde con un error de cuota.
"""
import io
from typing import List, Optional

from google.genai import errors, types

import config
from agents import llm

ESTILO = (
    "Photorealistic Catholic editorial photograph, cinematic, soft divine light from above, "
    "warm golden tones contrasting with cool blue shadows, sacred and hopeful atmosphere, "
    "subtle cross or a quiet reference to Michelangelo's Creation of Adam only when it fits, "
    "shallow depth of field, high detail. Absolutely no text, letters, words, logos or watermarks. "
    "No recognizable real people. Leave calm, darker space in the upper and lower thirds "
    "so captions can be placed over the image."
)

_PROPORCIONES = {"9:16": "vertical 9:16 (1080x1920)", "4:5": "vertical 4:5 (1080x1350)", "1:1": "square 1:1"}


def _modelos() -> List[str]:
    lista = [m.strip() for m in config.MODELO_IMAGEN.split(",") if m.strip()]
    try:
        for m in llm.cliente().models.list():
            nombre = (m.name or "").replace("models/", "")
            if "image" in nombre and "gemini" in nombre and nombre not in lista:
                lista.append(nombre)
    except Exception:
        pass
    return lista


def _extraer_imagen(respuesta) -> Optional[bytes]:
    for cand in respuesta.candidates or []:
        for parte in (cand.content.parts if cand.content else []) or []:
            datos = getattr(parte, "inline_data", None)
            if datos and datos.data:
                return datos.data
    return None


def _ajustar(datos: bytes, proporcion: str) -> bytes:
    """Recorta/ajusta a la medida exacta por si el modelo devolvió otra proporción."""
    from PIL import Image, ImageOps

    medidas = {"9:16": (1080, 1920), "4:5": (1080, 1350), "1:1": (1080, 1080)}[proporcion]
    img = Image.open(io.BytesIO(datos)).convert("RGB")
    img = ImageOps.fit(img, medidas, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def generar_imagen(idea: str, destino: str, proporcion: str = "9:16") -> str:
    """Genera una imagen en el estilo del podcast a partir de una idea (en español o inglés)
    y la guarda como JPG en destino. Devuelve la ruta."""
    pedido = (
        f"Create one {_PROPORCIONES.get(proporcion, proporcion)} image.\n"
        f"Scene: {idea.strip()}\n\nStyle: {ESTILO}"
    )
    ultimo_error: Optional[Exception] = None
    for modelo in _modelos():
        for con_config in (True, False):
            try:
                kwargs = {"response_modalities": ["IMAGE", "TEXT"]}
                if con_config:
                    kwargs["image_config"] = types.ImageConfig(aspect_ratio=proporcion)
                r = llm.cliente().models.generate_content(
                    model=modelo, contents=[pedido], config=types.GenerateContentConfig(**kwargs)
                )
                datos = _extraer_imagen(r)
                if datos:
                    with open(destino, "wb") as f:
                        f.write(_ajustar(datos, proporcion))
                    return destino
                ultimo_error = RuntimeError(f"{modelo} no devolvió imagen.")
                break
            except (errors.APIError, TypeError, ValueError) as e:
                ultimo_error = e
                # Si falló por el parámetro de proporción, se reintenta sin él; si no, siguiente modelo.
                if not con_config:
                    break
    mensaje = str(ultimo_error or "sin modelos de imagen disponibles")
    if "429" in mensaje or "quota" in mensaje.lower() or "RESOURCE_EXHAUSTED" in mensaje:
        raise RuntimeError(
            "Google no dejó crear la imagen por cuota. Para imágenes con IA suele hacer falta activar "
            "la facturación en el proyecto de tu clave en Google AI Studio. Mientras tanto, sube tu propia foto."
        )
    raise RuntimeError(f"No se pudo crear la imagen con IA: {mensaje[-300:]}")
