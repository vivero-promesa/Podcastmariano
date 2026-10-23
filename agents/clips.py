"""Estudio de clips: escucha el episodio grabado, elige los mejores momentos,
los corta, les pone subtítulos y escribe los textos para Instagram y TikTok."""
import os
from typing import List

from pydantic import BaseModel, Field

import config
from agents import llm, video
from agents.publicacion import hashtags_instagram_finales, hashtags_tiktok_finales


class ClipPropuesto(BaseModel):
    inicio: str = Field(description="Inicio en el audio, formato MM:SS o HH:MM:SS")
    fin: str = Field(description="Fin en el audio, formato MM:SS o HH:MM:SS. Duración entre 30 y 90 segundos")
    gancho: str = Field(description="Texto en pantalla de máximo 8 palabras que detenga el scroll")
    por_que_funciona: str = Field(description="Por qué este momento puede volverse viral")
    texto_instagram: str = Field(description="Caption para Instagram de 2 a 4 líneas, sin hashtags. Empieza con el momento o con una pregunta real que la gente se hace (nunca «nuevo episodio») y termina con una pregunta que invite a comentar")
    texto_tiktok: str = Field(description="Caption para TikTok de 1 a 2 líneas, sin hashtags. Empieza con una pregunta que la gente busca")
    hashtags_instagram: List[str] = Field(description="7 hashtags temáticos con #")
    hashtags_tiktok: List[str] = Field(description="3 hashtags temáticos con #")


class AnalisisEpisodio(BaseModel):
    clips: List[ClipPropuesto]
    capitulos: List[str] = Field(description="Capítulos del episodio para Spotify, formato «MM:SS Título»; el primero en 00:00")


class Segmento(BaseModel):
    inicio: float = Field(description="Segundo de inicio desde el comienzo del clip")
    fin: float = Field(description="Segundo de fin desde el comienzo del clip")
    texto: str = Field(description="Texto dicho, máximo 8 palabras")


class Transcripcion(BaseModel):
    segmentos: List[Segmento]


def a_segundos(marca: str) -> float:
    partes = [float(p) for p in marca.strip().replace(",", ".").split(":")]
    segundos = 0.0
    for p in partes:
        segundos = segundos * 60 + p
    return segundos


def a_marca(segundos: float) -> str:
    segundos = int(round(segundos))
    h, r = divmod(segundos, 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def analizar_episodio(ruta_mp3: str, cantidad: int = 5, contexto: str = "") -> AnalisisEpisodio:
    archivo = llm.subir_archivo(ruta_mp3, "audio/mpeg")
    pedido = f"""
Escucha completo este episodio de «{config.PODCAST['nombre']}».
{('Contexto: ' + contexto) if contexto else ''}

1. Elige los {cantidad} mejores momentos para clips verticales de 30 a 90 segundos.
   Criterios virales: frase que detiene el scroll en los primeros 3 segundos, se entiende sin contexto,
   genera emoción o debate, responde una pregunta que la gente busca ({", ".join(config.PALABRAS_BUSQUEDA[:6])}).
   El clip debe empezar al inicio de una frase y terminar al final de una idea.
2. Escribe los capítulos del episodio para la descripción de Spotify.
Usa marcas de tiempo exactas del audio. Tono: verdad con ternura, nunca condena.
"""
    return llm.estructurado(pedido, AnalisisEpisodio, temperatura=0.4, extra=[archivo])


def subtitular(ruta_clip: str) -> List[dict]:
    with open(ruta_clip, "rb") as f:
        parte = llm.audio_en_linea(f.read(), "audio/mpeg")
    pedido = (
        "Transcribe este audio en español, palabra por palabra, en segmentos cortos de 1 a 3 segundos "
        "(máximo 8 palabras cada uno) con sus tiempos exactos en segundos desde el inicio. "
        "Corrige solo la ortografía; no cambies las palabras."
    )
    t = llm.estructurado(pedido, Transcripcion, temperatura=0.0, extra=[parte])
    duracion = video.duracion_segundos(ruta_clip) or 60
    segmentos = []
    for s in t.segmentos:
        inicio, fin = max(0.0, s.inicio), min(duracion, s.fin)
        if fin > inicio and s.texto.strip():
            segmentos.append({"inicio": inicio, "fin": fin, "texto": s.texto})
    return segmentos


def textos_clip(clip: ClipPropuesto, enlace_episodio: str = "") -> dict:
    enlace = enlace_episodio or config.PODCAST["spotify"]
    ig = (
        f"{clip.texto_instagram.strip()}\n\n🎧 {config.PODCAST['llamado_spotify']}\n\n"
        + " ".join(hashtags_instagram_finales(clip.hashtags_instagram))
    )
    tt = f"{clip.texto_tiktok.strip()} 🎧 Episodio completo en Spotify (link en bio) " + " ".join(
        hashtags_tiktok_finales(clip.hashtags_tiktok)
    )
    return {"instagram": ig, "tiktok": tt, "enlace": enlace}


def producir_clip(
    episodio_mp3: str,
    inicio: float,
    fin: float,
    gancho: str,
    carpeta: str,
    nombre: str,
    fondo: str = None,
    con_subtitulos: bool = True,
    ajuste: str = "completa",
) -> dict:
    os.makedirs(carpeta, exist_ok=True)
    audio = os.path.join(carpeta, f"{nombre}.mp3")
    srt = os.path.join(carpeta, f"{nombre}.srt")
    mp4 = os.path.join(carpeta, f"{nombre}.mp4")
    video.cortar_audio(episodio_mp3, inicio, fin, audio)
    usar_srt = None
    if con_subtitulos:
        segmentos = subtitular(audio)
        if segmentos:
            video.escribir_srt(segmentos, srt)
            usar_srt = srt
    video.hacer_video_vertical(audio, usar_srt, gancho, mp4, fondo=fondo, ajuste=ajuste)
    return {"mp4": mp4, "srt": usar_srt, "mp3": audio}
