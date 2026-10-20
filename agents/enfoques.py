"""Propone enfoques nuevos para el episodio y resume lo que se profundizó,
usando el historial para no repetir temas."""
from typing import List

from pydantic import BaseModel, Field

import config
from agents import historial as hist
from agents import llm


class Enfoque(BaseModel):
    pregunta: str = Field(description="Pregunta o enfoque del episodio como lo escribiría la gente en el buscador, máximo 90 caracteres")
    por_que: str = Field(description="Por qué este enfoque es nuevo y útil para quien escucha, en una frase")
    puntos: List[str] = Field(description="3 o 4 puntos del documento que el episodio profundizaría")


class Propuesta(BaseModel):
    enfoques: List[Enfoque]


class Puntos(BaseModel):
    puntos: List[str] = Field(description="Entre 3 y 6 puntos concretos que el episodio profundizó, de máximo 15 palabras cada uno")


def proponer_enfoques(documentos: List[dict], historial: dict, cantidad: int = 3) -> List[Enfoque]:
    lista = "\n".join(f"- {config.etiqueta_documento(d)}" for d in documentos) or "- Tema libre (sin documento)"
    tratado = hist.resumen_tratado(historial, documentos) or "Nada todavía: es la primera vez que se trabajan."
    otros = "\n".join(
        f"- Episodio {e.get('numero', '?')}: {e.get('titulo', '')}" for e in historial.get("episodios", [])
    ) or "- Ninguno"
    varios = (
        "\nSon varios documentos: al menos un enfoque debe mostrar cómo evolucionó o se complementa la enseñanza entre ellos, en orden cronológico."
        if len(documentos) > 1 else ""
    )
    pedido = f"""
Podcast católico «{config.PODCAST['nombre']}». Audiencia: {config.PODCAST['audiencia']}.
Tono: verdad con ternura, nunca condena.

DOCUMENTO(S) DEL EPISODIO:
{lista}{varios}

YA SE TRATÓ DE ESTOS DOCUMENTOS (no lo repitas; sí puedes profundizar un punto que quedó corto):
{tratado}

TODOS LOS EPISODIOS PUBLICADOS (evita títulos parecidos):
{otros}

Propón {cantidad} enfoques distintos entre sí para el próximo episodio de 15-20 minutos.
- Cada pregunta debe responderse con lo que enseñan estos documentos.
- Usa las palabras que la gente realmente busca: {", ".join(config.PALABRAS_BUSQUEDA)}.
- Prioriza dudas reales de parejas con infertilidad, pérdidas o tratamientos.
- Nada de nombres en latín solos en la pregunta.
"""
    return llm.estructurado(pedido, Propuesta, temperatura=0.8).enfoques


def puntos_tratados(guion: str, enfoque: str) -> List[str]:
    pedido = (
        f"Enfoque del episodio: {enfoque}\n\n"
        "Lee el guion y lista los puntos doctrinales concretos que el episodio profundizó, "
        "para llevar un historial y no repetirlos en episodios futuros.\n\n"
        f"GUION:\n<<<\n{guion}\n>>>"
    )
    return llm.estructurado(pedido, Puntos, temperatura=0.2).puntos
