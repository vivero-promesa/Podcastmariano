"""Ajustes por voz o por texto: Elena dice (micrófono) o escribe qué quiere cambiar y la IA
devuelve solo los campos que cambian. Sirve para los clips y para el carrusel."""
from typing import List, Optional

from pydantic import BaseModel, Field

from agents import llm

VARIANTES = ["Suave", "Pulso", "Cine"]

REGLAS = (
    "Reglas del podcast: la pregunta en pantalla es directa, entre ¿?, máximo 8 palabras y con palabras que la gente "
    "busca; los textos terminan con una pregunta al público y conservan «Episodio completo en mi perfil» y los "
    "hashtags que ya tienen; tono de verdad con ternura, nunca condena, fiel a la doctrina católica."
)


class AjusteClip(BaseModel):
    entendido: str = Field(description="En una frase, qué entendiste que hay que cambiar")
    gancho: str = Field(default="", description="Nueva pregunta en pantalla; vacío si no cambia")
    texto_instagram: str = Field(default="", description="Texto completo nuevo para Instagram; vacío si no cambia")
    texto_tiktok: str = Field(default="", description="Texto completo nuevo para TikTok; vacío si no cambia")
    idea_imagen: str = Field(default="", description="Nueva idea de imagen EN INGLÉS para la IA; vacío si no cambia")
    variante: str = Field(default="", description=f"Una de {VARIANTES} si pide otro estilo de video; vacío si no cambia")
    empezar_antes: int = Field(default=0, description="Segundos para empezar antes (0 si no cambia)")
    terminar_despues: int = Field(default=0, description="Segundos para terminar después (0 si no cambia)")


class DiapositivaAjustada(BaseModel):
    titulo: str
    texto: str


class AjusteCarrusel(BaseModel):
    entendido: str = Field(description="En una frase, qué entendiste que hay que cambiar")
    diapositivas: List[DiapositivaAjustada] = Field(description="TODAS las diapositivas, con los cambios aplicados")
    caption: str = Field(description="Caption completo (igual si no cambia)")


def _partes(instruccion: str, audio: Optional[bytes], mime: str) -> tuple:
    extra = [llm.audio_en_linea(audio, mime)] if audio else []
    pedido = (f"Instrucción escrita: {instruccion}\n" if instruccion else "") + (
        "La instrucción está en el audio adjunto (Elena hablando).\n" if audio else "")
    return pedido, extra


def ajustar_clip(actual: dict, instruccion: str = "", audio: Optional[bytes] = None,
                 mime: str = "audio/wav") -> AjusteClip:
    """actual: gancho, texto_instagram, texto_tiktok, idea_imagen, variante, duracion."""
    pedido, extra = _partes(instruccion, audio, mime)
    pedido = f"""Eres el editor de redes del podcast. Aplica SOLO lo que Elena pide al clip; lo demás déjalo vacío.
{REGLAS}

Clip actual:
- Pregunta en pantalla: {actual.get('gancho', '')}
- Texto Instagram: {actual.get('texto_instagram', '')}
- Texto TikTok: {actual.get('texto_tiktok', '')}
- Idea de imagen: {actual.get('idea_imagen', '')}
- Estilo de video: {actual.get('variante', '')} (opciones: {', '.join(VARIANTES)})
- Duración: {actual.get('duracion', 0):.0f} s

{pedido}"""
    return llm.estructurado(pedido, AjusteClip, temperatura=0.4, extra=extra)


def ajustar_carrusel(diapositivas: list, caption: str, instruccion: str = "", audio: Optional[bytes] = None,
                     mime: str = "audio/wav") -> AjusteCarrusel:
    pedido, extra = _partes(instruccion, audio, mime)
    actuales = "\n".join(f"{n}. {d['titulo']} — {d['texto']}" for n, d in enumerate(diapositivas, 1))
    pedido = f"""Eres el editor de redes del podcast. Aplica SOLO lo que Elena pide al carrusel y devuelve todas las
diapositivas (títulos de máximo 8 palabras, textos de máximo 25). {REGLAS}

Diapositivas actuales:
{actuales}

Caption actual: {caption}

{pedido}"""
    return llm.estructurado(pedido, AjusteCarrusel, temperatura=0.4, extra=extra)
