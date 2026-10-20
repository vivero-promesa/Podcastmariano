"""Descarga el texto oficial de cada documento desde vatican.va.

Así el investigador y el censor trabajan sobre el documento real y no de memoria,
lo que evita citas inventadas.
"""
import re
from functools import lru_cache

import requests
from bs4 import BeautifulSoup

LIMITE_CARACTERES = 350_000  # ~90 mil tokens; cabe sin problema en Gemini


@lru_cache(maxsize=16)
def texto_oficial(url: str) -> str:
    if not url:
        return ""
    r = requests.get(url, timeout=40, headers={"User-Agent": "Mozilla/5.0 (PodcastBioetica)"})
    r.raise_for_status()
    sopa = BeautifulSoup(r.content, "html.parser")
    for basura in sopa(["script", "style", "nav", "header", "footer", "noscript"]):
        basura.decompose()
    texto = sopa.get_text("\n")
    texto = re.sub(r"[ \t\xa0]+", " ", texto)
    texto = re.sub(r"\n\s*\n+", "\n\n", texto).strip()
    return texto[:LIMITE_CARACTERES]
