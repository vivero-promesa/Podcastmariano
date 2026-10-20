"""Busca en vatican.va documentos nuevos del Papa y del Dicasterio para la Doctrina de la Fe
que todavía no están en el catálogo, y deja solo los que tratan la vida, la familia o la bioética."""
import re
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from agents import historial as hist
from agents import llm

AGENTE = {"User-Agent": "Mozilla/5.0 (PodcastBioetica)"}

# Documentos del Papa León XIV (índices oficiales en español)
SECCIONES_PAPA = {
    "encyclicals": "Encíclica",
    "apost_exhortations": "Exhortación apostólica",
    "apost_letters": "Carta apostólica",
    "motu_proprio": "Motu proprio",
}
INDICE_PAPA = "https://www.vatican.va/content/leo-xiv/es/{}.index.html"

# Documentos del Dicasterio para la Doctrina de la Fe (lista completa)
INDICE_DDF = "https://www.vatican.va/roman_curia/congregations/cfaith/doc_doc_index_sp.htm"
DDF_DESDE = 2020  # años anteriores ya están cubiertos por el catálogo base


class Candidato(BaseModel):
    url: str = Field(description="El enlace exacto recibido, sin cambios")
    titulo_corto: str = Field(description="Nombre corto del documento, ej.: Magnifica Humanitas o Dignitas Infinita")
    anio: int = Field(description="Año de publicación")
    tipo: str = Field(description="Encíclica, exhortación, carta apostólica, declaración, nota, etc.")
    tema: str = Field(description="Tema en pocas palabras, ej.: Dignidad humana e inteligencia artificial")
    relevante: bool = Field(description="True si trata vida humana, familia, matrimonio, sexualidad, procreación, fertilidad, bioética, salud o tecnología y dignidad humana")
    por_que: str = Field(description="Por qué sirve (o no) para el podcast, en una frase")


class Clasificacion(BaseModel):
    documentos: List[Candidato]


def _enlaces(url_indice: str, filtro) -> List[dict]:
    """Enlaces de un índice de vatican.va que pasan el filtro, uno por documento.

    Un mismo documento suele aparecer varias veces (título + «ES», «Español», «Italiano»…):
    se agrupan, se prefiere la versión en español y se toma el texto más largo como título."""
    r = requests.get(url_indice, timeout=30, headers=AGENTE)
    r.raise_for_status()
    sopa = BeautifulSoup(r.content, "html.parser")
    grupos = {}
    for a in sopa.find_all("a", href=True):
        href = urljoin(url_indice, a["href"]).split("#")[0]
        if not filtro(href):
            continue
        texto = " ".join(a.get_text(" ").split())
        clave = re.sub(r"_[a-z]{2}\.html?$", "", href)
        g = grupos.setdefault(clave, {"url": href, "titulo": ""})
        if "_sp.htm" in href or "/es/" in href:
            g["url"] = href
        if len(texto) > len(g["titulo"]):
            g["titulo"] = texto
    return [g for g in grupos.values() if g["titulo"]]


def _del_papa(seccion: str):
    marca = f"/content/leo-xiv/es/{seccion}/documents/"
    return lambda href: marca in href and href.endswith(".html")


def _ddf_reciente(href: str) -> bool:
    if "/cfaith/documents/" not in href or ".htm" not in href:
        return False
    fecha = re.search(r"_(\d{4})\d{4}_", href)
    return bool(fecha) and int(fecha.group(1)) >= DDF_DESDE


def buscar_documentos_nuevos(historial: dict) -> dict:
    """Devuelve {"nuevos": [Candidato relevantes], "descartados": [...], "errores": [...], "revisados": n}."""
    conocidas = hist.urls_conocidas(historial)
    candidatos, errores = [], []
    for seccion, tipo in SECCIONES_PAPA.items():
        try:
            for e in _enlaces(INDICE_PAPA.format(seccion), _del_papa(seccion)):
                candidatos.append({**e, "origen": f"León XIV · {tipo}"})
        except Exception as ex:
            errores.append(f"{tipo}: {ex}")
    try:
        for e in _enlaces(INDICE_DDF, _ddf_reciente):
            candidatos.append({**e, "origen": "Dicasterio para la Doctrina de la Fe"})
    except Exception as ex:
        errores.append(f"Dicasterio para la Doctrina de la Fe: {ex}")

    pendientes = [c for c in candidatos if hist._url_normal(c["url"]) not in conocidas]
    if not pendientes:
        return {"nuevos": [], "descartados": [], "errores": errores, "revisados": len(candidatos)}

    lista = "\n".join(f"- {c['url']} | {c['titulo']} | {c['origen']}" for c in pendientes)
    pedido = (
        "Estos documentos oficiales de vatican.va no están en el catálogo del podcast católico "
        "«La maternidad no siempre tiene cuna» (bioética, fertilidad, FIV, familia y dignidad humana). "
        "Clasifica cada uno. Devuelve uno por enlace, con el enlace exacto.\n\n" + lista
    )
    clasif = llm.estructurado(pedido, Clasificacion, temperatura=0.1).documentos
    validos = {c["url"] for c in pendientes}
    clasif = [c for c in clasif if c.url in validos]
    return {
        "nuevos": [c for c in clasif if c.relevante],
        "descartados": [c for c in clasif if not c.relevante],
        "errores": errores,
        "revisados": len(candidatos),
    }
