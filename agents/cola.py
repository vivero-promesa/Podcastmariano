"""Cola de Instagram: deja los Reels listos el jueves para que salgan solos a su hora.

Los videos se guardan como archivos de un lanzamiento de GitHub (etiqueta «cola-instagram»)
y la lista vive en cola_instagram.json, en la rama «borradores». Una tarea de GitHub Actions
(.github/workflows/publicar-instagram.yml) revisa la cola y publica lo que ya toca, aunque la
app de Streamlit esté dormida. Al publicar, el video se borra del lanzamiento.

Un solo hilo con aprobación: el clip armado entra como «por_aprobar» (la tarea de GitHub NUNCA
lo publica); solo cuando Elena aprueba la semana pasa a «pendiente» y sale solo a su hora.
"""
import base64
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import requests

from agents import historial as hist
from agents import planeacion as plan_mod

ARCHIVO = "cola_instagram.json"
RAMA = plan_mod.RAMA
ETIQUETA = "cola-instagram"
ZONA_BOGOTA = timezone(timedelta(hours=-5))
MAX_INTENTOS = 3
TIEMPO = 60


def _api(ruta: str) -> str:
    return f"{hist.API}/repos/{hist._repo()}{ruta}"


def _revisar(r: requests.Response, que: str):
    if r.status_code >= 400:
        raise RuntimeError(f"GitHub ({que}) respondió {r.status_code}: {r.text[:200]}")


def momento_de_publicar(fecha_iso: str) -> datetime:
    """Fecha del clip a la hora del horario único, en hora de Colombia."""
    return plan_mod.momento_clip(fecha_iso)


def ya_paso(fecha_iso: str, ahora: Optional[datetime] = None) -> bool:
    return (ahora or datetime.now(timezone.utc)) >= momento_de_publicar(fecha_iso)


# ─────────────────────────── La lista ───────────────────────────
def leer() -> Tuple[dict, Optional[str]]:
    r = requests.get(_api(f"/contents/{ARCHIVO}"), headers=hist._encabezados(), params={"ref": RAMA}, timeout=TIEMPO)
    if r.status_code == 404:
        return {"clips": []}, None
    _revisar(r, "leer la cola")
    datos = r.json()
    return json.loads(base64.b64decode(datos["content"]).decode("utf-8")), datos.get("sha")


def escribir(datos: dict, sha: Optional[str], mensaje: str) -> str:
    texto = json.dumps(datos, ensure_ascii=False, indent=2) + "\n"
    cuerpo = {"message": mensaje, "content": base64.b64encode(texto.encode("utf-8")).decode("ascii"), "branch": RAMA}
    if sha:
        cuerpo["sha"] = sha
    r = requests.put(_api(f"/contents/{ARCHIVO}"), headers=hist._encabezados(), json=cuerpo, timeout=TIEMPO)
    _revisar(r, "guardar la cola")
    return r.json()["content"]["sha"]


# ─────────────────────────── Los videos ───────────────────────────
def _lanzamiento() -> dict:
    r = requests.get(_api(f"/releases/tags/{ETIQUETA}"), headers=hist._encabezados(), timeout=TIEMPO)
    if r.status_code == 200:
        return r.json()
    r = requests.post(
        _api("/releases"), headers=hist._encabezados(), timeout=TIEMPO,
        json={"tag_name": ETIQUETA, "name": "Cola de Instagram", "prerelease": True,
              "body": "Videos esperando su hora de publicación. Se borran solos al publicarse."},
    )
    _revisar(r, "crear el lanzamiento")
    return r.json()


def borrar_archivo(nombre: str):
    for a in _lanzamiento().get("assets", []):
        if a["name"] == nombre:
            r = requests.delete(_api(f"/releases/assets/{a['id']}"), headers=hist._encabezados(), timeout=TIEMPO)
            _revisar(r, "borrar el video")


def subir_archivo(ruta: str, nombre: str, tipo: str) -> str:
    """Sube el archivo al lanzamiento (reemplaza si ya existe) y devuelve su dirección."""
    borrar_archivo(nombre)
    destino = _lanzamiento()["upload_url"].split("{")[0]
    with open(ruta, "rb") as f:
        r = requests.post(destino, params={"name": nombre}, data=f, timeout=600,
                          headers={**hist._encabezados(), "Content-Type": tipo})
    _revisar(r, "subir el video")
    return r.json()["browser_download_url"]


def descargar(url: str, destino: str) -> str:
    with requests.get(url, stream=True, timeout=300) as r:
        _revisar(r, "descargar el video")
        with open(destino, "wb") as f:
            for parte in r.iter_content(1024 * 1024):
                f.write(parte)
    return destino


# ─────────────────────────── Programar y cancelar ───────────────────────────
def identificador(semana_fecha: str, clip: int) -> str:
    return plan_mod.id_clip(semana_fecha, clip)


def programar(semana_fecha: str, clip: int, pilar: str, fecha_iso: str, mp4: str,
              portada: Optional[str], texto: str, ahora: Optional[datetime] = None,
              texto_tiktok: str = "", gancho: str = "", aprobado: bool = False) -> dict:
    """Deja un Reel en la cola. Por defecto queda «por_aprobar» (armado, esperando la aprobación).
    Si el clip ya estaba en la cola sin publicar, lo reemplaza; nunca repite uno publicado."""
    if ya_paso(fecha_iso, ahora):
        raise ValueError(f"La hora de este clip ({fecha_iso}) ya pasó. Cambia la semana o publícalo con 🚀.")
    cid = identificador(semana_fecha, clip)
    datos, sha = leer()
    previo = next((c for c in datos["clips"] if c["id"] == cid), None)
    if previo and previo["estado"] in ("publicado", "publicando"):
        raise ValueError("Este clip ya se publicó o se está publicando.")
    video = {"nombre": f"{cid}.mp4", "url": subir_archivo(mp4, f"{cid}.mp4", "video/mp4")}
    foto = None
    if portada and os.path.exists(portada):
        foto = {"nombre": f"{cid}.jpg", "url": subir_archivo(portada, f"{cid}.jpg", "image/jpeg")}
    nuevo = {
        "id": cid, "semana": semana_fecha, "clip": clip, "pilar": pilar,
        "publicar_en": momento_de_publicar(fecha_iso).isoformat(), "video": video, "portada": foto,
        "texto": texto, "texto_tiktok": texto_tiktok, "gancho": gancho, "fecha": fecha_iso,
        "estado": "pendiente" if aprobado else "por_aprobar", "intentos": 0, "enlace": "", "error": "",
    }
    datos["clips"] = [c for c in datos["clips"] if c["id"] != cid] + [nuevo]
    datos["clips"].sort(key=lambda c: c["publicar_en"])
    escribir(datos, sha, f"Cola de Instagram: {cid}")
    return nuevo


def aprobar(textos: dict, ahora: Optional[datetime] = None) -> Tuple[list, list]:
    """Aprueba los clips armados: {id: texto de Instagram final}. Pasan a «pendiente» y salen solos.
    Devuelve (aprobados, rechazados con motivo). Un clip cuya hora ya pasó no se aprueba."""
    datos, sha = leer()
    aprobados, fuera = [], []
    for c in datos.get("clips", []):
        if c["id"] not in textos or c["estado"] != "por_aprobar":
            continue
        if (ahora or datetime.now(timezone.utc)) >= datetime.fromisoformat(c["publicar_en"]):
            fuera.append((c["id"], "su hora ya pasó: devuélvelo o publícalo a mano con 🚀"))
            continue
        if textos[c["id"]]:
            c["texto"] = textos[c["id"]]
        c["estado"] = "pendiente"
        aprobados.append(c["id"])
    if aprobados:
        escribir(datos, sha, f"Cola de Instagram: aprobados {', '.join(aprobados)}")
    return aprobados, fuera


def cancelar(cid: str):
    datos, sha = leer()
    item = next((c for c in datos["clips"] if c["id"] == cid), None)
    if not item:
        return
    if item["estado"] in ("publicado", "publicando"):
        raise ValueError("Este clip ya se publicó o se está publicando.")
    datos["clips"] = [c for c in datos["clips"] if c["id"] != cid]
    escribir(datos, sha, f"Cola de Instagram: cancela {cid}")
    borrar_archivo(item["video"]["nombre"])
    if item.get("portada"):
        borrar_archivo(item["portada"]["nombre"])


def pendientes(datos: dict, ahora: Optional[datetime] = None) -> list:
    """Los clips a los que ya les llegó la hora."""
    ahora = ahora or datetime.now(timezone.utc)
    return [c for c in datos.get("clips", [])
            if c["estado"] == "pendiente" and datetime.fromisoformat(c["publicar_en"]) <= ahora]
