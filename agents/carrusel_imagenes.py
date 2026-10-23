"""Dibuja las diapositivas del carrusel de Instagram como imágenes listas para publicar.

Formato 1080x1350 (4:5, el que más espacio ocupa en el feed). Diseño fijo con los colores
del podcast: portada con título grande, diapositivas de contenido y cierre con llamado a
Spotify. Opcionalmente usa una foto de fondo (oscurecida para que el texto se lea).
"""
import io
import os
import zipfile
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

import config

ANCHO, ALTO = 1080, 1350
MARGEN = 90
FONDO = (29, 27, 47)        # mismo morado oscuro de los videos
ACENTO = (255, 205, 60)     # dorado
BLANCO = (255, 255, 255)
GRIS = (205, 203, 220)

_NEGRITA = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
_NORMAL = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _fuente(negrita: bool, tam: int) -> ImageFont.FreeTypeFont:
    for ruta in (_NEGRITA if negrita else _NORMAL):
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default(size=tam)


def _partir(draw: ImageDraw.ImageDraw, texto: str, fuente, ancho_max: int) -> List[str]:
    """Parte el texto en líneas que caben en ancho_max (respeta los saltos de línea)."""
    lineas = []
    for parrafo in (texto or "").split("\n"):
        palabras, actual = parrafo.split(), ""
        if not palabras:
            lineas.append("")
            continue
        for p in palabras:
            prueba = f"{actual} {p}".strip()
            if draw.textlength(prueba, font=fuente) <= ancho_max:
                actual = prueba
            else:
                if actual:
                    lineas.append(actual)
                actual = p
        lineas.append(actual)
    return lineas


def _bloque(draw, texto, negrita, tam_max, tam_min, ancho, alto_max, interlineado=1.25):
    """Busca el tamaño de letra más grande con el que el texto cabe en el espacio."""
    for tam in range(tam_max, tam_min - 1, -4):
        f = _fuente(negrita, tam)
        lineas = _partir(draw, texto, f, ancho)
        alto = int(len(lineas) * tam * interlineado)
        if alto <= alto_max:
            return f, lineas, alto, tam
    f = _fuente(negrita, tam_min)
    lineas = _partir(draw, texto, f, ancho)
    return f, lineas, int(len(lineas) * tam_min * interlineado), tam_min


def _escribir(draw, x, y, lineas, fuente, tam, color, interlineado=1.25):
    for linea in lineas:
        draw.text((x, y), linea, font=fuente, fill=color)
        y += int(tam * interlineado)
    return y


def _fondo(foto: Optional[str]) -> Image.Image:
    if not foto:
        return Image.new("RGB", (ANCHO, ALTO), FONDO)
    img = ImageOps.exif_transpose(Image.open(foto)).convert("RGB")
    img = ImageOps.fit(img, (ANCHO, ALTO), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2))
    capa = Image.new("RGB", (ANCHO, ALTO), FONDO)
    return Image.blend(img, capa, 0.62)


def dibujar_diapositiva(titulo: str, texto: str, n: int, total: int, foto: Optional[str] = None) -> Image.Image:
    img = _fondo(foto)
    d = ImageDraw.Draw(img)
    ancho_txt = ANCHO - 2 * MARGEN
    portada, cierre = n == 1, n == total

    # Encabezado: nombre del podcast y número de diapositiva
    f_peq = _fuente(True, 30)
    d.text((MARGEN, 70), config.PODCAST["nombre_corto"].upper(), font=f_peq, fill=ACENTO)
    num = f"{n}/{total}"
    d.text((ANCHO - MARGEN - d.textlength(num, font=f_peq), 70), num, font=f_peq, fill=GRIS)
    d.rectangle([MARGEN, 120, MARGEN + 90, 126], fill=ACENTO)

    zona_top, zona_fin = 190, ALTO - 200
    if portada:
        f_t, l_t, h_t, tam_t = _bloque(d, titulo, True, 104, 56, ancho_txt, 640, 1.15)
        f_x, l_x, h_x, tam_x = _bloque(d, texto, False, 44, 30, ancho_txt, 300)
        y = zona_top + max(0, (zona_fin - zona_top - h_t - 50 - h_x) // 2)
        y = _escribir(d, MARGEN, y, l_t, f_t, tam_t, BLANCO, 1.15) + 50
        _escribir(d, MARGEN, y, l_x, f_x, tam_x, GRIS)
    else:
        f_t, l_t, h_t, tam_t = _bloque(d, titulo, True, 76, 44, ancho_txt, 380, 1.15)
        y = _escribir(d, MARGEN, zona_top + 20, l_t, f_t, tam_t, ACENTO, 1.15) + 45
        f_x, l_x, h_x, tam_x = _bloque(d, texto, False, 50, 30, ancho_txt, zona_fin - y)
        _escribir(d, MARGEN, y, l_x, f_x, tam_x, BLANCO, 1.3)

    # Pie
    f_pie = _fuente(True, 34)
    usuario = config.PODCAST["instagram"]
    if cierre and not portada:
        pie = "Episodio completo en Spotify"
        d.rounded_rectangle([MARGEN, ALTO - 185, ANCHO - MARGEN, ALTO - 105], radius=40, fill=ACENTO)
        d.text(((ANCHO - d.textlength(pie, font=f_pie)) / 2, ALTO - 166), pie, font=f_pie, fill=FONDO)
        d.text(((ANCHO - d.textlength(usuario, font=f_pie)) / 2, ALTO - 85), usuario, font=f_pie, fill=GRIS)
    elif portada:
        d.text((MARGEN, ALTO - 140), usuario, font=f_pie, fill=GRIS)
        flecha = "Desliza  →"
        d.text((ANCHO - MARGEN - d.textlength(flecha, font=f_pie), ALTO - 140), flecha, font=f_pie, fill=ACENTO)
    else:
        d.text((ANCHO - MARGEN - d.textlength(usuario, font=f_pie), ALTO - 140), usuario, font=f_pie, fill=GRIS)
    return img


def crear_imagenes(diapositivas, foto: Optional[str] = None) -> List[bytes]:
    """diapositivas: objetos con .titulo y .texto. Devuelve PNG en bytes, en orden."""
    total = len(diapositivas)
    salida = []
    for n, dia in enumerate(diapositivas, 1):
        img = dibujar_diapositiva(dia.titulo, dia.texto, n, total, foto)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        salida.append(buf.getvalue())
    return salida


def zip_imagenes(imagenes: List[bytes], caption: str = "") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n, datos in enumerate(imagenes, 1):
            z.writestr(f"carrusel_{n:02d}.png", datos)
        if caption:
            z.writestr("caption.txt", caption)
    return buf.getvalue()
