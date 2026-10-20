"""Paquete de publicación: títulos que se encuentran en el buscador, descripción
para Spotify con enlaces a redes, hashtags y prompt de portada."""
from typing import List

from pydantic import BaseModel, Field

import config
from agents import llm


class PaqueteEpisodio(BaseModel):
    titulos: List[str] = Field(description="3 opciones de título, máximo 70 caracteres, empezando por lo que la gente busca")
    descripcion: str = Field(description="Descripción para Spotify de 3 párrafos cortos, sin enlaces")
    palabras_clave: List[str] = Field(description="8 palabras o frases de búsqueda")
    hashtags_instagram: List[str] = Field(description="8 hashtags con #, incluye católicos de México y Colombia")
    hashtags_tiktok: List[str] = Field(description="3 hashtags temáticos con #")
    texto_portada: str = Field(description="Máximo 5 palabras para la portada del episodio")
    prompt_portada: str = Field(description="Prompt en inglés para generar la portada con IA")


class TitulosNuevos(BaseModel):
    titulos: List[str] = Field(description="Un título nuevo por cada título original, en el mismo orden")


REGLAS_TITULO = f"""
REGLAS PARA TÍTULOS (Spotify depende de la búsqueda):
- Empieza con lo que la gente escribe: {", ".join(config.PALABRAS_BUSQUEDA)}.
- Formato sugerido: «¿La FIV es pecado? Lo que dice la Iglesia | Donum Vitae».
- El nombre del documento va al final, nunca solo el nombre en latín.
- Ortografía impecable (mayúsculas solo al inicio y en nombres propios).
- Máximo 70 caracteres.
"""

ESTILO_PORTADA = (
    "photorealistic Catholic editorial style, soft divine light, warm vs cold contrast, "
    "subtle cross or Creation of Adam reference, no text, 1:1"
)


def crear_paquete(guion: str, tema: str, documento: str) -> PaqueteEpisodio:
    pedido = (
        f"Podcast: {config.PODCAST['nombre']}\nTema: {tema}\nDocumento: {documento}\n"
        f"{REGLAS_TITULO}\nEstilo de portada: {ESTILO_PORTADA}\n\nGUION:\n<<<\n{guion}\n>>>"
    )
    return llm.estructurado(pedido, PaqueteEpisodio, temperatura=0.6)


def hashtags_tiktok_finales(temas: List[str]) -> List[str]:
    """TikTok: 3 a 5 hashtags, siempre con #fyp y #parati."""
    base = [h if h.startswith("#") else f"#{h}" for h in temas if h.strip()]
    base = [h for h in base if h.lower() not in ("#fyp", "#parati")][:3]
    return base + ["#fyp", "#parati"]


def hashtags_instagram_finales(temas: List[str]) -> List[str]:
    """Instagram: 5 a 10 hashtags, siempre con el de la marca."""
    base = [h if h.startswith("#") else f"#{h}" for h in temas if h.strip()]
    marca = config.PODCAST["hashtag_marca"]
    base = [h for h in base if h.lower() != marca.lower()][:9]
    return base + [marca]


def descripcion_spotify(paquete: PaqueteEpisodio, capitulos: List[str] = None) -> str:
    p = config.PODCAST
    partes = [paquete.descripcion.strip()]
    if capitulos:
        partes.append("Capítulos:\n" + "\n".join(capitulos))
    partes.append(
        f"Síguenos en Instagram {p['instagram']}: {p['instagram_url']}\n"
        f"Y en TikTok {p['tiktok']}: {p['tiktok_url']}\n"
        "Si este episodio te ayudó, compártelo con alguien que lo necesite."
    )
    partes.append(" ".join(hashtags_instagram_finales(paquete.hashtags_instagram)[:5]))
    return "\n\n".join(partes)


def mejorar_titulos(titulos: List[str]) -> List[str]:
    pedido = (
        f"Podcast: {config.PODCAST['nombre']}\n{REGLAS_TITULO}\n"
        "Reescribe estos títulos de episodios ya publicados, corrigiendo ortografía:\n"
        + "\n".join(f"- {t}" for t in titulos)
    )
    return llm.estructurado(pedido, TitulosNuevos, temperatura=0.4).titulos
