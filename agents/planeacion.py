"""Planeación de contenido: estrategia, calendario de episodios, plan semanal de clips,
métricas y banco de ideas.

El plan vive en planeacion.json, en la rama «borradores» del repositorio (la misma del
guardado automático). Así guardar el plan NO reinicia la app, que se despliega desde
«main». Necesita el mismo GITHUB_TOKEN que el historial; sin token se guarda en el
servidor (se pierde si la app se reinicia) y se ofrece descargar el archivo.
"""
import base64
import json
import os
import tempfile
from datetime import date, timedelta
from typing import List, Optional

import requests

from agents import historial as hist

ARCHIVO = "planeacion.json"
RAMA = "borradores"
RUTA_LOCAL = os.path.join(tempfile.gettempdir(), ARCHIVO)

ESTADOS = ["Por producir", "Investigación", "Guion listo", "Grabado", "Publicado"]

# Los 3 clips de cada semana: uno por pilar (modelo vigente: 3 clips, mismo archivo en
# Instagram y TikTok, todos programados el jueves).
PILARES = [
    {
        "clip": 1,
        "pilar": "Pregunta real",
        "dia": "Viernes (con el episodio)",
        "objetivo": "Que te encuentren: responde lo que la gente escribe en el buscador.",
        "ejemplo": "«¿La FIV es pecado?»",
    },
    {
        "clip": 2,
        "pilar": "Lo que dice la Iglesia",
        "dia": "Lunes",
        "objetivo": "Autoridad: una cita verificada explicada con palabras de a pie.",
        "ejemplo": "«El hijo es un don, no un derecho»",
    },
    {
        "clip": 3,
        "pilar": "Esperanza y acompañamiento",
        "dia": "Miércoles",
        "objetivo": "Comunidad: ternura para quien vive la infertilidad e invitación a escuchar.",
        "ejemplo": "«Si llevas años esperando, esto es para ti»",
    },
]

SERIES = [
    "Antes de la FIV: lo que nadie te explica",
    "El matrimonio abierto a la vida",
    "Ciencia, tecnología y dignidad",
    "Episodio especial",
]

# Lista del viernes (lo que se hace cada semana).
LISTA_VIERNES = [
    "Episodio subido a Spotify for Creators con título y descripción de la app",
    "Capítulos con minutos agregados a la descripción de Spotify",
    "Enlace de la bio de Instagram y TikTok cambiado al episodio nuevo",
    "Los 3 clips programados (jueves): viernes, lunes y miércoles",
    "Mismos 3 clips subidos a YouTube Shorts",
    "Episodio guardado en el historial de la app",
    "Responder comentarios del fin de semana",
]

# Calendario inicial de 12 semanas (se puede editar todo desde la app).
# (serie, documento(s) del catálogo, enfoque, invitado)
_PLAN_BASE = [
    (0, ["DV"], "¿La FIV es pecado? Lo que la Iglesia sí dice (y lo que no)", False),
    (0, ["DP"], "Embriones congelados: ¿qué pasa con ellos y qué puedo hacer?", False),
    (0, ["CIC"], "Infertilidad y FIV: lo que enseña el Catecismo", False),
    (0, ["LIBRE"], "Vientre de alquiler: ¿por qué la Iglesia dice no? (Dignitas Infinita)", True),
    (1, ["HV"], "¿Los anticonceptivos son pecado? Humanae Vitae explicada", False),
    (1, ["FC"], "La familia que no llega: ¿qué espera la Iglesia de una pareja infértil?", False),
    (1, ["GS"], "¿Para qué es el matrimonio? Amor y apertura a la vida", False),
    (1, ["AL"], "Navidad sin hijos: esperanza para las parejas que esperan", True),
    (2, ["CV"], "¿Todo lo que la ciencia puede hacer, se debe hacer?", False),
    (2, ["LS"], "Ecología humana: el cuerpo también es casa común", False),
    (2, ["VS"], "¿Existe el bien y el mal objetivo en la fertilidad?", False),
    (2, ["MH"], "Inteligencia artificial y dignidad humana: lo que dice León XIV", True),
]


def proximo_viernes(desde: Optional[date] = None) -> date:
    """El viernes siguiente (si hoy es viernes, el de la otra semana)."""
    hoy = desde or date.today()
    dias = (4 - hoy.weekday()) % 7 or 7
    return hoy + timedelta(days=dias)


def _numerar_series(semanas: List[dict]) -> List[dict]:
    """Pone «1/4», «2/4»… según el orden de cada serie en el calendario."""
    totales = {}
    for s in semanas:
        totales[s.get("serie", "")] = totales.get(s.get("serie", ""), 0) + 1
    vistos = {}
    for s in semanas:
        serie = s.get("serie", "")
        vistos[serie] = vistos.get(serie, 0) + 1
        s["parte"] = f"{vistos[serie]}/{totales[serie]}" if serie and serie != "Episodio especial" else ""
    return semanas


def plan_por_defecto(desde: Optional[date] = None) -> dict:
    inicio = proximo_viernes(desde)
    semanas = []
    for i, (serie, docs, enfoque, invitado) in enumerate(_PLAN_BASE):
        semanas.append({
            "fecha": (inicio + timedelta(weeks=i)).isoformat(),
            "serie": SERIES[serie],
            "documentos": docs,
            "enfoque": enfoque,
            "invitado": invitado,
            "estado": "Por producir",
            "notas": "",
        })
    return {
        "version": 1,
        "semanas": _numerar_series(semanas),
        "metricas": [],
        "ideas": [],
        "lista_viernes": {},
    }


def _normalizar(datos: Optional[dict]) -> dict:
    if not datos or not datos.get("semanas"):
        return plan_por_defecto()
    datos.setdefault("metricas", [])
    datos.setdefault("ideas", [])
    datos.setdefault("lista_viernes", {})
    datos["semanas"] = sorted(datos["semanas"], key=lambda s: s.get("fecha") or "")
    _numerar_series(datos["semanas"])
    return datos


# ─────────────────────────── Guardar y cargar ───────────────────────────
def _api(ruta: str) -> str:
    return f"{hist.API}/repos/{hist._repo()}{ruta}"


def _asegurar_rama():
    r = requests.get(_api(f"/branches/{RAMA}"), headers=hist._encabezados(), timeout=20)
    if r.status_code == 200:
        return
    base = requests.get(_api(f"/git/ref/heads/{hist._rama()}"), headers=hist._encabezados(), timeout=20)
    base.raise_for_status()
    c = requests.post(
        _api("/git/refs"), headers=hist._encabezados(),
        json={"ref": f"refs/heads/{RAMA}", "sha": base.json()["object"]["sha"]}, timeout=20,
    )
    if c.status_code not in (201, 422):
        c.raise_for_status()


def _leer_github():
    r = requests.get(_api(f"/contents/{ARCHIVO}"), headers=hist._encabezados(), params={"ref": RAMA}, timeout=20)
    if r.status_code != 200:
        return None, None
    datos = r.json()
    return json.loads(base64.b64decode(datos["content"]).decode("utf-8")), datos.get("sha")


def cargar() -> dict:
    """Plan guardado: primero GitHub, luego el servidor; si no hay, el plan inicial de 12 semanas."""
    if hist.puede_guardar():
        try:
            datos, _ = _leer_github()
            if datos:
                return _normalizar(datos)
        except Exception:
            pass
    try:
        with open(RUTA_LOCAL, encoding="utf-8") as f:
            return _normalizar(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return plan_por_defecto()


def a_json(plan: dict) -> str:
    return json.dumps(plan, ensure_ascii=False, indent=2) + "\n"


def guardar(plan: dict, mensaje: str = "Planeación del podcast") -> str:
    """Guarda en el servidor y en GitHub (rama «borradores»). Devuelve dónde quedó."""
    plan = _normalizar(plan)
    texto = a_json(plan)
    with open(RUTA_LOCAL, "w", encoding="utf-8") as f:
        f.write(texto)
    if not hist.puede_guardar():
        return "servidor"
    _asegurar_rama()
    _, sha = _leer_github()
    cuerpo = {
        "message": mensaje,
        "content": base64.b64encode(texto.encode("utf-8")).decode("ascii"),
        "branch": RAMA,
    }
    if sha:
        cuerpo["sha"] = sha
    r = requests.put(_api(f"/contents/{ARCHIVO}"), headers=hist._encabezados(), json=cuerpo, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"GitHub respondió {r.status_code}: {r.text[:300]}")
    return "github"


# ─────────────────────────── Consultas ───────────────────────────
def semana_actual(plan: dict, hoy: Optional[date] = None) -> Optional[dict]:
    """La primera semana del calendario cuya fecha es hoy o después."""
    hoy = (hoy or date.today()).isoformat()
    for s in plan.get("semanas", []):
        if (s.get("fecha") or "") >= hoy:
            return s
    return None


def siguiente_de(plan: dict, semana: dict) -> Optional[dict]:
    """La semana que viene después de esta (para el avance al cierre del episodio)."""
    semanas = plan.get("semanas", [])
    for i, s in enumerate(semanas):
        if s is semana or s.get("fecha") == semana.get("fecha"):
            return semanas[i + 1] if i + 1 < len(semanas) else None
    return None


def agregar_semana(plan: dict) -> dict:
    ultima = plan["semanas"][-1]["fecha"] if plan.get("semanas") else None
    fecha = (date.fromisoformat(ultima) + timedelta(weeks=1)) if ultima else proximo_viernes()
    nueva = {
        "fecha": fecha.isoformat(), "serie": "Episodio especial", "documentos": ["LIBRE"],
        "enfoque": "", "invitado": False, "estado": "Por producir", "notas": "",
    }
    plan["semanas"].append(nueva)
    _numerar_series(plan["semanas"])
    return nueva
