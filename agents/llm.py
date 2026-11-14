"""Conexión única con Gemini usando el SDK oficial google-genai.

Si Google responde "modelo saturado" (503), "demasiadas peticiones" (429) u otro
error temporal del servidor, la app reintenta sola con esperas crecientes y, si el
modelo principal sigue caído, prueba uno por uno los modelos de respaldo
(GEMINI_MODEL_RESPALDO, lista separada por comas; por defecto
gemini-flash-latest y gemini-flash-lite-latest, que usa otra capacidad de Google).
"""
import random
import re
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
# Esperas entre intentos (segundos) con el mismo modelo, antes de pasar al siguiente.
_ESPERAS = (5, 15, 30)


class FaltaClave(RuntimeError):
    pass


class GeminiOcupado(RuntimeError):
    """Google sigue saturado después de todos los reintentos y modelos de respaldo."""


class GeminiSinCuota(GeminiOcupado):
    """Se agotó la cuota de la clave de Gemini (error 429): esperar minutos no lo arregla."""


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
    """Modelo principal seguido de los de respaldo (sin repetidos)."""
    respaldo = getattr(config, "MODELO_RESPALDO", "") or ""
    lista = [config.MODELO] + [m.strip() for m in respaldo.split(",")]
    vistos = []
    for m in lista:
        if m and m not in vistos:
            vistos.append(m)
    return vistos


def _es_temporal(e: Exception) -> bool:
    codigo = getattr(e, "code", None)
    if isinstance(e, errors.ServerError):
        return True
    return isinstance(e, errors.APIError) and codigo in _CODIGOS_TEMPORALES


def _es_cuota(e: Exception) -> bool:
    """429 = se agotó la cuota o el límite de peticiones de la clave."""
    return isinstance(e, errors.APIError) and getattr(e, "code", None) == 429


def _es_cuota_diaria(e: Exception) -> bool:
    """La cuota del día no vuelve esperando unos segundos: no vale la pena reintentar."""
    texto = str(e)
    return _es_cuota(e) and ("PerDay" in texto or "per day" in texto.lower())


def _espera_cuota(e: Exception) -> float:
    """Segundos que Google pide esperar (retryDelay), entre 10 y 60."""
    m = re.search(r"retry(?:Delay)?[^0-9]{0,20}(\d+(?:\.\d+)?)\s*s", str(e), re.IGNORECASE)
    segundos = float(m.group(1)) if m else 40.0
    return min(60.0, max(10.0, segundos)) + random.uniform(0, 2)


def _detalle(e: Optional[Exception]) -> str:
    """Mensaje original de Google, corto, para no volver a ocultar la causa real."""
    if e is None:
        return ""
    texto = " ".join(str(e).split())
    return texto[:300] + ("…" if len(texto) > 300 else "")


def _generar(contenidos: list, cfg: types.GenerateContentConfig):
    """generate_content con reintentos y modelos de respaldo ante errores temporales."""
    ultimo_error: Optional[Exception] = None
    errores_temporales = []
    for modelo in _modelos():
        for intento in range(len(_ESPERAS) + 1):
            try:
                return cliente().models.generate_content(model=modelo, contents=contenidos, config=cfg)
            except errors.APIError as e:
                if not _es_temporal(e):
                    # Modelo de respaldo inexistente o sin acceso: pasar al siguiente
                    # sin ocultar el error original del modelo principal.
                    if modelo != config.MODELO and ultimo_error is not None:
                        break
                    raise
                ultimo_error = e
                errores_temporales.append(e)
                if _es_cuota_diaria(e):
                    # Cuota del día agotada para este modelo: probar el siguiente sin esperar.
                    break
                if _es_cuota(e):
                    # Límite por minuto del plan gratuito: reintentar varias veces seguidas solo
                    # gasta más cuota. Se espera lo que Google indica (máx. 60 s) UNA sola vez
                    # y luego se pasa al modelo de respaldo, que tiene su propia cuota.
                    if intento >= 1:
                        break
                    time.sleep(_espera_cuota(e))
                    continue
                if intento < len(_ESPERAS):
                    time.sleep(_ESPERAS[intento] + random.uniform(0, 3))
    if errores_temporales and all(_es_cuota(e) for e in errores_temporales):
        diaria = any(_es_cuota_diaria(e) for e in errores_temporales)
        cuando = (
            "La cuota diaria se renueva a medianoche de California (entre las 2 y las 3 a. m. hora de Colombia). "
            if diaria
            else "Si es el límite por minuto, vuelve a intentarlo en 1 o 2 minutos; si persiste, es la cuota del día. "
        )
        raise GeminiSinCuota(
            "Se acabó la cuota de tu clave de Gemini (error 429 de Google, no de la app). "
            + cuando
            + "Para no esperar, activa la facturación en el proyecto de la clave en aistudio.google.com. "
            + "Lo que ya hiciste en la app no se pierde. "
            + f"Detalle de Google: {_detalle(ultimo_error)}"
        ) from ultimo_error
    raise GeminiOcupado(
        "Gemini está saturado en este momento (error temporal de Google, no de la app). "
        "Espera unos minutos y vuelve a intentarlo; lo que ya hiciste en la app no se pierde. "
        f"Detalle de Google: {_detalle(ultimo_error)}"
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
