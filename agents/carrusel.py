"""Carrusel de Instagram listo para Canva (Bulk Create)."""
from typing import List

from pydantic import BaseModel, Field

import config
from agents import llm


class Diapositiva(BaseModel):
    titulo: str = Field(description="Máximo 8 palabras")
    texto: str = Field(description="Máximo 25 palabras")


class Carrusel(BaseModel):
    diapositivas: List[Diapositiva]
    caption: str = Field(description="Caption de Instagram de 3 a 5 líneas, sin hashtags")
    hashtags: List[str] = Field(description="8 hashtags con #")


def crear_carrusel(tema: str, cantidad: int = 7) -> Carrusel:
    pedido = f"""
Crea un carrusel de Instagram de {cantidad} diapositivas para «{config.PODCAST['nombre']}» sobre: {tema}
- Diapositiva 1: gancho con una pregunta que la gente busca ({", ".join(config.PALABRAS_BUSQUEDA[:5])}).
- Del medio: una idea por diapositiva, fiel a la doctrina católica, con ternura.
- Penúltima: frase para guardar y compartir.
- Última: «Escucha el episodio completo en Spotify — enlace en la bio» y {config.PODCAST['instagram']}.
"""
    return llm.estructurado(pedido, Carrusel, temperatura=0.6)
