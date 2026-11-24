"""Paquete de publicación: títulos que se encuentran en el buscador, descripción
para Spotify con enlaces a redes, hashtags y prompt de portada."""
from typing import List

from pydantic import BaseModel, Field

import config
from agents import llm


class PaqueteEpisodio(BaseModel):
    titulos: List[str] = Field(description="3 opciones de título: empiezan con una pregunta concreta con palabras de búsqueda, lo esencial en los primeros 35 caracteres, máximo 70 caracteres")
    descripcion: str = Field(description="Descripción para Spotify de 3 párrafos cortos, sin enlaces")
    palabras_clave: List[str] = Field(description="8 palabras o frases de búsqueda")
    hashtags_instagram: List[str] = Field(description="8 hashtags con #, incluye católicos de México y Colombia")
    hashtags_tiktok: List[str] = Field(description="3 hashtags temáticos con #")
    texto_portada: str = Field(description="Máximo 4 palabras grandes para la plantilla fija de portada (la pregunta o idea central)")
    prompt_portada: str = Field(description="Prompt en inglés para la ÚNICA imagen de la plantilla fija de portada: una sola escena, sin texto")


class TitulosNuevos(BaseModel):
    titulos: List[str] = Field(description="Un título nuevo por cada título original, en el mismo orden")


REGLAS_TITULO = f"""
REGLAS PARA TÍTULOS (Spotify depende de la búsqueda y corta el título en unos 35 caracteres):
- SIEMPRE empieza con una pregunta concreta entre ¿?, con palabras que la gente escribe: {", ".join(config.PALABRAS_BUSQUEDA)}.
- Lo importante va en los primeros 35 caracteres: la pregunta debe entenderse sola aunque se corte el resto.
- El título dice qué gana quien escucha (una respuesta, una duda resuelta), no solo el tema.
- Ejemplos buenos: «¿Es pecado la FIV? Lo que dice la Iglesia», «¿Qué pasa con los embriones congelados?», «¿Infertilidad y fe? Lo que nadie te explica».
- Ejemplos malos: «La cultura de la muerte.», «El drama de los embriones…», «Dignitas Personae: …» (no son preguntas, no se buscan, no dicen qué gana la persona).
- Nunca empieces con el nombre del documento ni con palabras en latín; si se menciona el documento, va al final después de «|».
- Ortografía impecable (mayúsculas solo al inicio y en nombres propios).
- Máximo 70 caracteres.
"""

# Plantilla FIJA de portada: todos los episodios se ven iguales para que se
# reconozca el programa en miniatura. Colores de la marca (los mismos de los clips).
PLANTILLA_PORTADA = (
    "Plantilla fija, igual en todos los episodios: cuadrada 1:1, fondo azul noche #1D1B2F, "
    "UNA sola imagen al centro y máximo 4 palabras grandes en dorado, legibles en miniatura. "
    "Sin más texto, sin logos extra y sin cambiar de estilo entre episodios."
)

ESTILO_PORTADA = (
    "single subject, one simple photorealistic Catholic editorial image, soft divine golden light, "
    "deep midnight blue background (#1D1B2F), minimal composition with empty space at the top for large text, "
    "readable as a small thumbnail, no text, no letters, no collage, 1:1"
)


def crear_paquete(guion: str, tema: str, documento: str) -> PaqueteEpisodio:
    pedido = (
        f"Podcast: {config.PODCAST['nombre']}\nTema: {tema}\nDocumento: {documento}\n"
        f"{REGLAS_TITULO}\nPortada: {PLANTILLA_PORTADA}\nEstilo de la imagen de portada: {ESTILO_PORTADA}\n\nGUION:\n<<<\n{guion}\n>>>"
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
        "Reescribe estos títulos de episodios ya publicados siguiendo TODAS las reglas (pregunta al inicio, "
        "palabras de búsqueda en los primeros 35 caracteres) y corrigiendo ortografía:\n"
        + "\n".join(f"- {t}" for t in titulos)
    )
    return llm.estructurado(pedido, TitulosNuevos, temperatura=0.4).titulos
