"""Edición con ffmpeg: normaliza el audio, corta clips y arma videos verticales 9:16
con gancho en pantalla, onda de sonido y subtítulos grandes (formato Reels/TikTok)."""
import os
import shutil
import subprocess
import textwrap
from typing import List, Optional

import config

FUENTE_NEGRITA = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FUENTE_NORMAL = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
COLOR_FONDO = "0x1d1b2f"
COLOR_ONDA = "gold"


def ffmpeg_disponible() -> bool:
    return shutil.which("ffmpeg") is not None


def _correr(args: List[str], cwd: Optional[str] = None):
    r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg falló: {r.stderr.strip()[-800:]}")


def duracion_segundos(ruta: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", ruta],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def normalizar_audio(origen: str, destino: str):
    """Convierte cualquier audio (m4a, wav, mp3) a MP3 mono, que Gemini acepta siempre."""
    _correr(["-i", origen, "-vn", "-ac", "1", "-ar", "44100", "-b:a", "96k", destino])


def cortar_audio(origen: str, inicio: float, fin: float, destino: str,
                 margen_antes: float = 0.3, margen_despues: float = 0.8):
    """Corta con un pequeño margen y desvanecido suave para que no quede «cortado» a mitad de palabra."""
    inicio = max(0.0, inicio - margen_antes)
    fin = fin + margen_despues
    total = duracion_segundos(origen)
    if total:
        fin = min(fin, total)
    dur = max(0.5, fin - inicio)
    salida = max(0.0, dur - 0.4)
    _correr([
        "-ss", f"{inicio:.2f}", "-to", f"{fin:.2f}", "-i", origen,
        "-af", f"afade=t=in:st=0:d=0.15,afade=t=out:st={salida:.2f}:d=0.4",
        "-ac", "1", "-b:a", "128k", destino,
    ])


def _tiempo_srt(seg: float) -> str:
    ms = int(round(seg * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def escribir_srt(segmentos: List[dict], destino: str):
    """segmentos: [{"inicio": 0.0, "fin": 2.5, "texto": "..."}]"""
    lineas = []
    for i, s in enumerate(segmentos, 1):
        texto = "\n".join(textwrap.wrap(s["texto"].strip(), 28))
        lineas.append(f"{i}\n{_tiempo_srt(s['inicio'])} --> {_tiempo_srt(s['fin'])}\n{texto}\n")
    with open(destino, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))


def _copiar(origen: str, destino: str):
    if os.path.abspath(origen) != os.path.abspath(destino):
        shutil.copy(origen, destino)


def hacer_video_vertical(
    audio: str,
    srt: Optional[str],
    gancho: str,
    destino: str,
    fondo: Optional[str] = None,
    ajuste: str = "completa",
):
    """Arma un MP4 1080x1920 con: fondo (imagen o color), gancho arriba, onda al centro,
    subtítulos abajo y llamado a Spotify al pie."""
    carpeta = os.path.dirname(os.path.abspath(destino))
    # ffmpeg es delicado con rutas raras: copiamos todo con nombres simples en la misma carpeta.
    _copiar(audio, os.path.join(carpeta, "_a.mp3"))
    with open(os.path.join(carpeta, "_gancho.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(textwrap.wrap(gancho.strip(), 20)))
    with open(os.path.join(carpeta, "_pie.txt"), "w", encoding="utf-8") as f:
        f.write(f"Episodio completo en Spotify\n{config.PODCAST['instagram']}")
    if srt:
        _copiar(srt, os.path.join(carpeta, "_s.srt"))

    entradas = ["-i", "_a.mp3"]
    if fondo:
        nombre_fondo = "_fondo" + (os.path.splitext(fondo)[1] or ".jpg")
        _copiar(fondo, os.path.join(carpeta, nombre_fondo))
        entradas += ["-loop", "1", "-i", nombre_fondo]
        if ajuste == "llenar":
            # Amplía la foto hasta llenar 9:16 (recorta los bordes).
            base = (
                "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                "drawbox=x=0:y=0:w=iw:h=ih:color=black@0.45:t=fill,fps=30[bg]"
            )
        else:
            # Foto completa, sin recortar, sobre una copia difuminada que llena la pantalla.
            base = (
                "[1:v]split=2[f1][f2];"
                "[f1]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:3,"
                "drawbox=x=0:y=0:w=iw:h=ih:color=black@0.55:t=fill[b0];"
                "[f2]scale=1080:1920:force_original_aspect_ratio=decrease,"
                "drawbox=x=0:y=0:w=iw:h=ih:color=black@0.25:t=fill[fg];"
                "[b0][fg]overlay=(W-w)/2:(H-h)/2,fps=30[bg]"
            )
    else:
        entradas += ["-f", "lavfi", "-i", f"color=c={COLOR_FONDO}:s=1080x1920:r=30"]
        base = "[1:v]format=yuv420p[bg]"

    filtros = [
        base,
        f"[0:a]showwaves=s=1080x300:mode=cline:rate=30:scale=sqrt:draw=full:colors={COLOR_ONDA},format=rgba[onda]",
        "[bg][onda]overlay=0:820[v1]",
        (
            f"[v1]drawtext=fontfile={FUENTE_NEGRITA}:textfile=_gancho.txt:fontsize=68:fontcolor=white:"
            "line_spacing=14:box=1:boxcolor=black@0.55:boxborderw=28:x=(w-text_w)/2:y=230[v2]"
        ),
        (
            f"[v2]drawtext=fontfile={FUENTE_NORMAL}:textfile=_pie.txt:fontsize=38:fontcolor=white@0.9:"
            "line_spacing=10:x=(w-text_w)/2:y=h-230[v3]"
        ),
    ]
    salida = "[v3]"
    if srt:
        filtros.append(
            "[v3]subtitles=_s.srt:force_style='FontName=DejaVu Sans,Bold=1,FontSize=13,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,"
            "BorderStyle=3,Outline=3,Shadow=0,Alignment=2,MarginV=70'[v4]"
        )
        salida = "[v4]"

    _correr(
        [
            *entradas,
            "-filter_complex", ";".join(filtros),
            "-map", salida, "-map", "0:a",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
            os.path.basename(destino),
        ],
        cwd=carpeta,
    )
