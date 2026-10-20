"""Conexión única con Gemini usando el SDK oficial google-genai.

Si Google responde "modelo saturado" (503), "demasiadas peticiones" (429) u otro
error temporal del servidor, la app reintenta sola con esperas crecientes y, si el
modelo principal sigue caído, prueba con el modelo de respaldo (GEMINI_MODEL_RESPALDO,
por defecto gemini-flash-latest).
"""
import time
from typing import Optional, Type, TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

import config

T = TypeVar("T", bound=BaseModel)

_cliente: Optional[genai.Client] = None

# Errores temporales de Google que vale la pena reintentar.
_CODIGOS_TEMPORALES = {429, 500, 502, 503, 504}
# Esperas entre intentos (segundos) con el mismo modelo.
_ESPERAS = (4, 10, 20)


class FaltaClave(RuntimeError):
    pass


class GeminiOcupado(RuntimeError):
    """Google sigue saturado después de todos los reintentos."""


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


def _modelos() -> list:
    """Modelo principal y, si es distinto, el de respaldo."""
    principal = config.MODELO
    respaldo = getattr(config, "MODELO_RESPALDO", "") or ""
    return [principal] + ([respaldo] if respaldo and respaldo != principal else [])


def _es_temporal(e: Exception) -> bool:
    codigo = getattr(e, "code", None)
    if isinstance(e, errors.ServerError):
        return True
    return isinstance(e, errors.APIError) and codigo in _CODIGOS_TEMPORALES


def _generar(contenidos: list, cfg: types.GenerateContentConfig):
    """generate_content con reintentos y modelo de respaldo ante errores temporales."""
    ultimo_error: Optional[Exception] = None
    for modelo in _modelos():
        for intento in range(len(_ESPERAS) + 1):
            try:
                return cliente().models.generate_content(model=modelo, contents=contenidos, config=cfg)
            except errors.APIError as e:
                if not _es_temporal(e):
                    # Modelo de respaldo inexistente o sin acceso: no ocultar el error original.
                    if modelo != config.MODELO and ultimo_error is not None:
                        break
                    raise
                ultimo_error = e
                if intento < len(_ESPERAS):
                    time.sleep(_ESPERAS[intento])
    raise GeminiOcupado(
        "Gemini está saturado en este momento (error temporal de Google). "
        "Espera unos minutos y vuelve a intentarlo; lo que ya hiciste en la app no se pierde."
    ) from ultimo_error


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
    r = _generar(contenidos, cfg)
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
    r = _generar(contenidos, cfg)
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
