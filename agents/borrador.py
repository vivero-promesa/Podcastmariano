"""Guardado automático del episodio en curso (Estudio de producción).

Streamlit borra lo que tienes en pantalla cuando se recarga la página, se corta la
conexión, la app se duerme o se actualiza el código. Para no perder el trabajo, cada
avance se guarda solo en dos lugares:

1. Un archivo en el servidor (sobrevive a recargar la página o a perder la conexión).
2. GitHub, en la rama «borradores» (sobrevive a reinicios y actualizaciones de la app).
   Se usa una rama aparte para que guardar NO reinicie la app (la app se despliega
   desde «main»). Necesita el mismo GITHUB_TOKEN que el historial.

Al abrir el Estudio de producción, si hay trabajo guardado, aparece el botón
«Recuperar mi trabajo».
"""
import base64
import hashlib
import importlib
import json
import os
import tempfile
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import requests
from pydantic import BaseModel

from agents import historial as hist

ARCHIVO = "borrador_produccion.json"
RAMA = "borradores"
RUTA_LOCAL = os.path.join(tempfile.gettempdir(), ARCHIVO)

# Lo que se guarda del Estudio de producción.
CLAVES = [
    "docs_sel", "tema_input", "duracion", "enfoques",
    "inv", "rev_inv", "ok_inv",
    "guion", "rev_guion", "ok_guion",
    "paquete", "guardado",
]


# ─────────────────────────── Convertir a JSON y de vuelta ───────────────────────────
def _a_json(valor):
    if isinstance(valor, BaseModel):
        cls = type(valor)
        return {"__modelo__": f"{cls.__module__}:{cls.__qualname__}", "datos": valor.model_dump(mode="json")}
    if isinstance(valor, (list, tuple)):
        return [_a_json(v) for v in valor]
    if isinstance(valor, dict):
        return {str(k): _a_json(v) for k, v in valor.items()}
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    return str(valor)


def _de_json(valor):
    if isinstance(valor, dict) and "__modelo__" in valor:
        modulo, nombre = valor["__modelo__"].split(":", 1)
        cls = importlib.import_module(modulo)
        for parte in nombre.split("."):
            cls = getattr(cls, parte)
        return cls.model_validate(valor["datos"])
    if isinstance(valor, list):
        return [_de_json(v) for v in valor]
    if isinstance(valor, dict):
        return {k: _de_json(v) for k, v in valor.items()}
    return valor


def _resumen(estado: dict) -> str:
    tema = (estado.get("tema_input") or "").strip() or "sin tema"
    if estado.get("paquete"):
        paso = "paquete de publicación"
    elif estado.get("guion"):
        paso = "guion"
    elif estado.get("inv"):
        paso = "investigación"
    elif estado.get("enfoques"):
        paso = "enfoques"
    else:
        paso = "inicio"
    return f"{tema} — llegaste hasta: {paso}"


def empaquetar(session_state) -> Optional[dict]:
    """Toma lo importante de la sesión. None si todavía no hay nada que valga la pena guardar."""
    estado = {k: _a_json(session_state.get(k)) for k in CLAVES if session_state.get(k) is not None}
    if not any(estado.get(k) for k in ("enfoques", "inv", "guion", "paquete")):
        return None
    return {
        "fecha": datetime.now(ZoneInfo("America/Bogota")).strftime("%d/%m/%Y %I:%M %p"),
        "resumen": _resumen(session_state),
        "estado": estado,
    }


# ─────────────────────────── GitHub (rama «borradores») ───────────────────────────
def _api(ruta: str) -> str:
    return f"{hist.API}/repos/{hist._repo()}{ruta}"


def _asegurar_rama():
    r = requests.get(_api(f"/branches/{RAMA}"), headers=hist._encabezados(), timeout=20)
    if r.status_code == 200:
        return
    base = requests.get(_api(f"/git/ref/heads/{hist._rama()}"), headers=hist._encabezados(), timeout=20)
    base.raise_for_status()
    sha = base.json()["object"]["sha"]
    c = requests.post(
        _api("/git/refs"), headers=hist._encabezados(),
        json={"ref": f"refs/heads/{RAMA}", "sha": sha}, timeout=20,
    )
    if c.status_code not in (201, 422):  # 422 = ya existe
        c.raise_for_status()


def _sha_github() -> Optional[str]:
    r = requests.get(
        _api(f"/contents/{ARCHIVO}"), headers=hist._encabezados(), params={"ref": RAMA}, timeout=20
    )
    return r.json().get("sha") if r.status_code == 200 else None


def _guardar_github(texto: str):
    _asegurar_rama()
    cuerpo = {
        "message": "Borrador automático del Estudio de producción",
        "content": base64.b64encode(texto.encode("utf-8")).decode("ascii"),
        "branch": RAMA,
    }
    sha = _sha_github()
    if sha:
        cuerpo["sha"] = sha
    r = requests.put(_api(f"/contents/{ARCHIVO}"), headers=hist._encabezados(), json=cuerpo, timeout=30)
    r.raise_for_status()


def _cargar_github() -> Optional[dict]:
    r = requests.get(
        _api(f"/contents/{ARCHIVO}"), headers=hist._encabezados(), params={"ref": RAMA}, timeout=20
    )
    if r.status_code != 200:
        return None
    return json.loads(base64.b64decode(r.json()["content"]).decode("utf-8"))


# ─────────────────────────── Lo que usa la página ───────────────────────────
def cargar() -> Optional[dict]:
    """Borrador más reciente: primero GitHub, si no, el archivo del servidor."""
    if hist.puede_guardar():
        try:
            datos = _cargar_github()
            if datos:
                return datos
        except Exception:
            pass
    try:
        with open(RUTA_LOCAL, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def autoguardar(session_state) -> Optional[str]:
    """Guarda solo si algo cambió desde el último guardado. Devuelve la hora o None."""
    datos = empaquetar(session_state)
    if not datos:
        return None
    huella = hashlib.sha1(json.dumps(datos["estado"], sort_keys=True).encode("utf-8")).hexdigest()
    if huella == session_state.get("_borrador_huella"):
        return session_state.get("_borrador_hora")
    texto = json.dumps(datos, ensure_ascii=False, indent=2)
    with open(RUTA_LOCAL, "w", encoding="utf-8") as f:
        f.write(texto)
    if hist.puede_guardar():
        try:
            _guardar_github(texto)
        except Exception:
            pass  # queda la copia del servidor; se reintenta en el próximo cambio
    session_state["_borrador_huella"] = huella
    session_state["_borrador_hora"] = datos["fecha"]
    return datos["fecha"]


def restaurar(session_state, datos: dict):
    """Pone de vuelta en pantalla el trabajo guardado (se usa como on_click)."""
    for clave, valor in (datos.get("estado") or {}).items():
        try:
            session_state[clave] = _de_json(valor)
        except Exception:
            pass
    session_state["_borrador"] = None


def borrar():
    """Elimina el borrador (al empezar un episodio nuevo)."""
    try:
        os.remove(RUTA_LOCAL)
    except FileNotFoundError:
        pass
    if hist.puede_guardar():
        try:
            sha = _sha_github()
            if sha:
                requests.delete(
                    _api(f"/contents/{ARCHIVO}"), headers=hist._encabezados(),
                    json={"message": "Borrador descartado", "sha": sha, "branch": RAMA}, timeout=20,
                )
        except Exception:
            pass
