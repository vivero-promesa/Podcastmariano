"""Historial de episodios y documentos agregados al catálogo.

Vive en historial_episodios.json, dentro de este mismo repositorio de GitHub, para que
no se pierda cuando Streamlit Cloud reinicia la app. Cada guardado queda como un commit,
así que siempre se puede ver qué cambió y cuándo.

Para guardar, la app necesita GITHUB_TOKEN en los Secrets (permiso de escritura en el
contenido del repositorio). Sin token, la app lee la copia del repositorio desplegado
y ofrece descargar el archivo actualizado para subirlo a mano.
"""
import base64
import json
import os
import re
from datetime import date
from typing import List, Optional, Tuple

import requests

import config

ARCHIVO = "historial_episodios.json"
RUTA_LOCAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ARCHIVO)
API = "https://api.github.com"


def _repo() -> str:
    return config._secreto("GITHUB_REPO", "vivero-promesa/Podcastmariano")


def _rama() -> str:
    return config._secreto("GITHUB_BRANCH", "main")


def _token() -> str:
    return config._secreto("GITHUB_TOKEN")


def puede_guardar() -> bool:
    return bool(_token())


def _encabezados() -> dict:
    return {
        "Authorization": f"Bearer {_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _normalizar(datos: Optional[dict]) -> dict:
    datos = dict(datos or {})
    datos.setdefault("episodios", [])
    datos.setdefault("documentos_extra", [])
    return datos


def cargar() -> Tuple[dict, Optional[str]]:
    """Devuelve (historial, sha). Con token lee la versión más reciente de GitHub;
    sin token, la copia que trae el repositorio desplegado."""
    if _token():
        try:
            r = requests.get(
                f"{API}/repos/{_repo()}/contents/{ARCHIVO}",
                headers=_encabezados(), params={"ref": _rama()}, timeout=20,
            )
            if r.status_code == 404:
                return _normalizar(None), None
            r.raise_for_status()
            datos = r.json()
            texto = base64.b64decode(datos["content"]).decode("utf-8")
            return _normalizar(json.loads(texto)), datos["sha"]
        except Exception:
            pass  # si GitHub falla, seguimos con la copia local
    try:
        with open(RUTA_LOCAL, encoding="utf-8") as f:
            return _normalizar(json.load(f)), None
    except (FileNotFoundError, json.JSONDecodeError):
        return _normalizar(None), None


def a_json(historial: dict) -> str:
    return json.dumps(historial, ensure_ascii=False, indent=2) + "\n"


def guardar(historial: dict, mensaje: str) -> str:
    """Guarda el historial en GitHub como un commit. Devuelve el enlace del commit."""
    if not _token():
        raise RuntimeError("Falta GITHUB_TOKEN en los Secrets de Streamlit: no puedo guardar en GitHub.")
    _, sha = cargar()  # sha más reciente, para no pisar otro guardado
    cuerpo = {
        "message": mensaje,
        "content": base64.b64encode(a_json(historial).encode("utf-8")).decode("ascii"),
        "branch": _rama(),
    }
    if sha:
        cuerpo["sha"] = sha
    r = requests.put(
        f"{API}/repos/{_repo()}/contents/{ARCHIVO}", headers=_encabezados(), json=cuerpo, timeout=30
    )
    if r.status_code >= 400:
        raise RuntimeError(f"GitHub respondió {r.status_code}: {r.text[:300]}")
    return r.json().get("commit", {}).get("html_url", "")


# ─────────────────────────── Catálogo ───────────────────────────
def catalogo(historial: dict) -> List[dict]:
    """Documentos fijos de config.py + los agregados desde la app."""
    claves = {d["clave"] for d in config.DOCUMENTOS}
    extra = [d for d in historial.get("documentos_extra", []) if d.get("clave") not in claves]
    return config.DOCUMENTOS + extra


def _url_normal(url: str) -> str:
    return (url or "").strip().lower().replace("http://", "https://").rstrip("/")


def urls_conocidas(historial: dict) -> set:
    return {_url_normal(d.get("url")) for d in catalogo(historial) if d.get("url")}


def _clave_nueva(titulo: str, existentes: set) -> str:
    base = re.sub(r"[^A-Z0-9]", "", titulo.upper())[:10] or "DOC"
    clave, n = base, 2
    while clave in existentes:
        clave, n = f"{base}{n}", n + 1
    return clave


def agregar_documento(historial: dict, titulo: str, anio: Optional[int], tema: str, url: str) -> dict:
    """Agrega un documento al catálogo (si su enlace no estaba ya)."""
    if _url_normal(url) in urls_conocidas(historial):
        raise ValueError("Ese documento ya está en el catálogo.")
    existentes = {d["clave"] for d in catalogo(historial)}
    doc = {
        "clave": _clave_nueva(titulo, existentes),
        "titulo": titulo.strip(),
        "anio": anio,
        "tema": tema.strip(),
        "url": url.strip(),
        "agregado": date.today().isoformat(),
    }
    historial["documentos_extra"].append(doc)
    return doc


# ─────────────────────────── Episodios ───────────────────────────
def episodios_de(historial: dict, clave: str) -> List[dict]:
    return [e for e in historial.get("episodios", []) if clave in e.get("documentos", [])]


def claves_tratadas(historial: dict) -> set:
    return {c for e in historial.get("episodios", []) for c in e.get("documentos", [])}


def resumen_tratado(historial: dict, documentos: List[dict]) -> str:
    """Texto con lo que ya se trató de estos documentos (para no repetir)."""
    lineas = []
    for d in documentos:
        for e in episodios_de(historial, d["clave"]):
            puntos = "; ".join(e.get("puntos") or []) or "sin detalle de puntos"
            lineas.append(f"- {d['titulo']} · episodio {e.get('numero', '?')} «{e.get('titulo', '')}»: {puntos}")
    return "\n".join(lineas)


def agregar_episodio(historial: dict, documentos: List[dict], enfoque: str, titulo: str, puntos: List[str]) -> dict:
    numeros = [e.get("numero", 0) or 0 for e in historial.get("episodios", [])]
    nuevo = {
        "numero": (max(numeros) if numeros else 0) + 1,
        "fecha": date.today().isoformat(),
        "documentos": [d["clave"] for d in documentos],
        "documentos_titulos": [d["titulo"] for d in documentos],
        "enfoque": enfoque.strip(),
        "titulo": titulo.strip(),
        "puntos": [p.strip() for p in puntos if p and p.strip()],
    }
    historial["episodios"].append(nuevo)
    return nuevo
