"""Conexión única con Gemini usando el SDK oficial google-genai."""
import time
from typing import Optional, Type, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

import config

T = TypeVar("T", bound=BaseModel)

_cliente: Optional[genai.Client] = None


class FaltaClave(RuntimeError):
    pass


def cliente() -> genai.Client:
    global _cliente
    if _cliente is None:
        clave = config.api_key()
        if not clave:
            raise FaltaClave(
                "Falta GOOGLE_API_KEY. Agrégala en .env (local/Codespaces) o en los Secrets de Streamlit Cloud."
            )
        _cliente = genai.Client(api_key=clave)
    return _cliente


def texto(
    prompt: str,
    sistema: Optional[str] = None,
    temperatura: float = 0.5,
    buscar_web: bool = False,
    extra: Optional[list] = None,
) -> str:
    """Respuesta en texto libre. Con buscar_web=True usa Google Search como fuente."""
    herramientas = [types.Tool(google_search=types.GoogleSearch())] if buscar_web else None
    cfg = types.GenerateContentConfig(
        system_instruction=sistema, temperature=temperatura, tools=herramientas
    )
    contenidos = [*(extra or []), prompt]
    r = cliente().models.generate_content(model=config.MODELO, contents=contenidos, config=cfg)
    return (r.text or "").strip()


def estructurado(
    prompt: str,
    esquema: Type[T],
    sistema: Optional[str] = None,
    temperatura: float = 0.3,
    extra: Optional[list] = None,
) -> T:
    """Respuesta validada con un modelo Pydantic (salida JSON estructurada)."""
    cfg = types.GenerateContentConfig(
        system_instruction=sistema,
        temperature=temperatura,
        response_mime_type="application/json",
        response_schema=esquema,
    )
    contenidos = [*(extra or []), prompt]
    r = cliente().models.generate_content(model=config.MODELO, contents=contenidos, config=cfg)
    if isinstance(r.parsed, esquema):
        return r.parsed
    return esquema.model_validate_json(r.text)


def subir_archivo(ruta: str, mime: str):
    """Sube un archivo (audio largo) a Gemini y espera a que quede listo."""
    archivo = cliente().files.upload(file=ruta, config={"mime_type": mime})
    for _ in range(60):
        estado = getattr(archivo.state, "name", str(archivo.state))
        if estado != "PROCESSING":
            break
        time.sleep(2)
        archivo = cliente().files.get(name=archivo.name)
    if getattr(archivo.state, "name", "") == "FAILED":
        raise RuntimeError("Gemini no pudo procesar el audio.")
    return archivo


def audio_en_linea(datos: bytes, mime: str = "audio/mpeg"):
    """Parte de audio corta (menos de 20 MB) para enviar directo en la petición."""
    return types.Part.from_bytes(data=datos, mime_type=mime)
