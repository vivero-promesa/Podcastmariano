"""Edición con ffmpeg: normaliza el audio, corta clips y arma videos verticales 9:16
con gancho en pantalla, onda de sonido, subtítulos grandes estilo Reels
y llamado a Spotify, todo dentro de la «zona segura» que no tapan los botones de
Instagram y TikTok.

Diseño (1080x1920):
  y   0-200   libre (ahí van los menús de Instagram/TikTok)
  y 250       gancho (texto grande con caja)
  y 860-1120  onda de sonido dorada
  y ~1360     subtítulos (2 líneas máx., palabras grandes)
  y 1450      «Episodio completo en Spotify» (pastilla dorada) + @usuario
  y 1650+     libre (ahí va el texto de la publicación y los botones)
"""
import os
import re
import shutil
import subprocess
import textwrap
from typing import List, Optional

import config

FUENTE_NEGRITA = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FUENTE_NORMAL = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
COLOR_FONDO = "0x1d1b2f"
COLOR_ONDA = "gold"
ANCHO, ALTO = 1080, 1920


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
    """Corta con un pequeño margen y desvanecido suave para que no quede «cortado» a mitad de palabra.
    Además deja el volumen parejo y fuerte (-14 LUFS, el estándar de Instagram y TikTok)."""
    inicio = max(0.0, inicio - margen_antes)
    fin = fin + margen_despues
    total = duracion_segundos(origen)
    if total:
        fin = min(fin, total)
    dur = max(0.5, fin - inicio)
    salida = max(0.0, dur - 0.4)
    _correr([
        "-ss", f"{inicio:.2f}", "-to", f"{fin:.2f}", "-i", origen,
        "-af", (
            "highpass=f=70,"
            "loudnorm=I=-14:TP=-1.5:LRA=11,"
            f"afade=t=in:st=0:d=0.15,afade=t=out:st={salida:.2f}:d=0.4"
        ),
        "-ac", "1", "-ar", "44100", "-b:a", "128k", destino,
    ])


# ─────────────────────────── Subtítulos ───────────────────────────

def _tiempo_srt(seg: float) -> str:
    ms = int(round(seg * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _tiempo_ass(seg: float) -> str:
    cs = int(round(seg * 100))
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6_000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def trocear(segmentos: List[dict], max_palabras: int = 4) -> List[dict]:
    """Parte cada segmento en trozos de pocas palabras (se leen de un vistazo, como en los Reels),
    repartiendo el tiempo según el largo de cada trozo."""
    salida = []
    for s in segmentos:
        palabras = s["texto"].split()
        if not palabras:
            continue
        trozos = [palabras[i:i + max_palabras] for i in range(0, len(palabras), max_palabras)]
        # Evita un último trozo de una sola palabra suelta.
        if len(trozos) > 1 and len(trozos[-1]) == 1:
            trozos[-2] += trozos.pop()
        total_letras = sum(len(" ".join(t)) for t in trozos) or 1
        t = s["inicio"]
        dur = max(0.2, s["fin"] - s["inicio"])
        for trozo in trozos:
            texto = " ".join(trozo)
            fin = t + dur * len(texto) / total_letras
            salida.append({"inicio": t, "fin": fin, "texto": texto})
            t = fin
    return salida


def escribir_srt(segmentos: List[dict], destino: str):
    """segmentos: [{"inicio": 0.0, "fin": 2.5, "texto": "..."}] — archivo .srt para descargar."""
    lineas = []
    for i, s in enumerate(segmentos, 1):
        texto = "\n".join(textwrap.wrap(s["texto"].strip(), 32))
        lineas.append(f"{i}\n{_tiempo_srt(s['inicio'])} --> {_tiempo_srt(s['fin'])}\n{texto}\n")
    with open(destino, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))


def escribir_ass(segmentos: List[dict], destino: str):
    """Subtítulos grandes estilo Reels/TikTok: letra gruesa, borde negro, 3-4 palabras por vez,
    centrados a la altura de la zona segura. La palabra más larga de cada trozo va en dorado."""
    cabecera = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {ANCHO}
PlayResY: {ALTO}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Reel,DejaVu Sans,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,1,0,0,0,100,100,0,0,1,7,3,2,110,110,560,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    eventos = []
    for s in trocear(segmentos):
        texto = re.sub(r"[{}\\]", "", s["texto"]).strip()
        if not texto:
            continue
        palabras = texto.split()
        # Resalta en dorado la palabra más larga (suele ser la que lleva el sentido).
        clave = max(range(len(palabras)), key=lambda k: len(re.sub(r"\W", "", palabras[k])))
        if len(palabras) > 1:
            palabras[clave] = r"{\c&H3CCDFF&}" + palabras[clave] + r"{\c&HFFFFFF&}"
        # Pequeño «salto» al aparecer: escala de 85% a 100% en 0,12 s.
        efecto = r"{\fscx85\fscy85\t(0,120,\fscx100\fscy100)}"
        eventos.append(
            f"Dialogue: 0,{_tiempo_ass(s['inicio'])},{_tiempo_ass(s['fin'])},Reel,,0,0,0,,{efecto}{' '.join(palabras)}"
        )
    with open(destino, "w", encoding="utf-8") as f:
        f.write(cabecera + "\n".join(eventos) + "\n")


def preparar_fondo(foto: str, destino: str, ajuste: str = "completa", tam=(ANCHO, ALTO)):
    """Fondo vertical listo para el video.
    «llenar»: la foto amplía y recorta hasta llenar la pantalla.
    «completa»: la foto entera, sin recortar, sobre una copia difuminada de sí misma."""
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

    ancho, alto = tam
    img = ImageOps.exif_transpose(Image.open(foto)).convert("RGB")
    lleno = ImageOps.fit(img, (ancho, alto), Image.LANCZOS)
    if ajuste == "llenar":
        base = ImageEnhance.Brightness(lleno).enhance(0.6)
    else:
        chico = lleno.resize((ancho // 6, alto // 6), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
        base = ImageEnhance.Brightness(chico.resize((ancho, alto), Image.BILINEAR)).enhance(0.45)
        frente = ImageOps.contain(img, (ancho, alto), Image.LANCZOS)
        frente = ImageEnhance.Brightness(frente).enhance(0.8)
        base.paste(frente, ((ancho - frente.width) // 2, (alto - frente.height) // 2))
    base.save(destino)
    return destino


def _copiar(origen: str, destino: str):
    if os.path.abspath(origen) != os.path.abspath(destino):
        shutil.copy(origen, destino)


# ─────────────────────────── Video vertical ───────────────────────────

def hacer_video_vertical(
    audio: str,
    subtitulos: Optional[str],
    gancho: str,
    destino: str,
    fondo: Optional[str] = None,
    ajuste: str = "completa",
    movimiento: bool = True,
):
    """Arma un MP4 1080x1920 con: fondo (imagen o color), gancho arriba, onda al centro,
    subtítulos grandes y llamado a Spotify.

    subtitulos: ruta a un .ass (estilo Reels) o .srt.
    movimiento: con imagen, la foto se mueve muy despacio (retiene más que una foto quieta).
    """
    carpeta = os.path.dirname(os.path.abspath(destino))
    dur = max(1.0, duracion_segundos(audio))
    # ffmpeg es delicado con rutas raras: copiamos todo con nombres simples en la misma carpeta.
    _copiar(audio, os.path.join(carpeta, "_a.mp3"))
    with open(os.path.join(carpeta, "_gancho.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(textwrap.wrap(gancho.strip(), 20)))
    with open(os.path.join(carpeta, "_spotify.txt"), "w", encoding="utf-8") as f:
        f.write("Episodio completo en Spotify")
    with open(os.path.join(carpeta, "_usuario.txt"), "w", encoding="utf-8") as f:
        f.write(config.PODCAST["instagram"])
    nombre_subs = None
    if subtitulos:
        nombre_subs = "_s" + os.path.splitext(subtitulos)[1].lower()
        _copiar(subtitulos, os.path.join(carpeta, nombre_subs))

    entradas = ["-i", "_a.mp3"]
    if fondo:
        # El fondo se prepara una sola vez con Pillow (recorte, difuminado, oscurecido);
        # ffmpeg solo lo desplaza cuadro a cuadro. Así el video sale varias veces más rápido.
        ancho_f, alto_f = (1166, 2074) if movimiento else (ANCHO, ALTO)
        preparar_fondo(fondo, os.path.join(carpeta, "_fondo.png"), ajuste, (ancho_f, alto_f))
        entradas += ["-loop", "1", "-framerate", "30", "-i", "_fondo.png"]
        if movimiento:
            base = f"[1:v]crop=1080:1920:x=(iw-ow)/2:y=(ih-oh)*t/{dur:.2f},setsar=1,format=yuv420p[bg]"
        else:
            base = "[1:v]setsar=1,format=yuv420p[bg]"
    else:
        entradas += ["-f", "lavfi", "-i", f"color=c={COLOR_FONDO}:s=1080x1920:r=30"]
        base = "[1:v]format=yuv420p[bg]"

    filtros = [
        base,
        f"[0:a]showwaves=s=1080x260:mode=cline:rate=30:scale=sqrt:draw=full:colors={COLOR_ONDA},format=rgba[onda]",
        "[bg][onda]overlay=0:860[v1]",
        (
            f"[v1]drawtext=fontfile={FUENTE_NEGRITA}:textfile=_gancho.txt:fontsize=70:fontcolor=white:"
            "line_spacing=14:box=1:boxcolor=black@0.6:boxborderw=30:x=(w-text_w)/2:y=250:"
            "alpha='min(1,t/0.25)'[v2]"
        ),
        (
            f"[v2]drawtext=fontfile={FUENTE_NEGRITA}:textfile=_spotify.txt:fontsize=40:fontcolor=0x1d1b2f:"
            "box=1:boxcolor=gold@0.95:boxborderw=22:x=(w-text_w)/2:y=1450,"
            f"drawtext=fontfile={FUENTE_NORMAL}:textfile=_usuario.txt:fontsize=34:fontcolor=white@0.9:"
            "x=(w-text_w)/2:y=1528[v3]"
        ),
    ]
    salida = "[v3]"
    if nombre_subs:
        filtros.append(f"[v3]subtitles={nombre_subs}[v4]")
        salida = "[v4]"

    _correr(
        [
            *entradas,
            "-filter_complex", ";".join(filtros),
            "-map", salida, "-map", "0:a",
            "-t", f"{dur:.2f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
            "-r", "30", "-g", "60",
            "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-movflags", "+faststart",
            os.path.basename(destino),
        ],
        cwd=carpeta,
    )


def portada_clip(video_mp4: str, gancho: str, destino: str, segundo: float = 1.0):
    """Portada JPG 1080x1920 para el clip: el primer cuadro del video con el gancho.
    Sirve como portada del Reel en Instagram y para elegir la portada en TikTok."""
    _correr(["-ss", f"{segundo:.2f}", "-i", video_mp4, "-frames:v", "1", "-q:v", "2", destino])
