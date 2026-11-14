"""Recorte del texto oficial para ahorrar tokens de Gemini (plan gratuito).

Antes se enviaba el documento entero (hasta ~150 mil tokens) a la Investigadora y otra vez
al Censor. Con la clave gratuita eso agota el límite de tokens por minuto de Google (error 429)
y la investigación nunca termina.

Ahora solo se envían los párrafos del documento que tienen que ver con el tema del episodio
(más el inicio del documento, que dice qué es y quién lo escribe). Las citas se siguen copiando
del texto oficial real: el Censor verifica contra los MISMOS párrafos que leyó la Investigadora.
"""
import re
import unicodedata
from typing import List

# Palabras vacías que no ayudan a saber de qué trata un párrafo.
_VACIAS = set(
    """
    a al algo algun alguna algunas alguno algunos ante antes aqui asi aun bajo bien cada como con contra cual
    cuales cuando de del desde donde dos el ella ellas ello ellos en entre era eran es esa esas ese eso esos
    esta estan estas este esto estos fue fueron ha han hasta hay la las le les lo los mas me mi mismo mucho
    muy nada ni no nos nuestra nuestro o otra otras otro otros para pero poco por porque puede pueden que
    quien se segun ser si sin sino sobre son su sus tambien tan tanto te tiene tienen todo todos tu un una
    uno unos y ya yo permite iglesia catolica dice ensena explicado episodio cuales puede deben debe hacer
    """.split()
)

# Inicio del documento que siempre se incluye (título, autor, introducción).
_INICIO = 2_500


def _normal(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _raiz(palabra: str) -> str:
    """Raíz muy simple: «génicas», «genica», «gen» se parecen lo suficiente."""
    return palabra[:6] if len(palabra) > 6 else palabra


# Palabras de la gente → cómo las nombran los documentos de la Iglesia.
_SINONIMOS = {
    "genica": ["genet", "genoma", "germin", "eugene"],
    "geneti": ["genica", "genoma", "germin", "eugene"],
    "bebe": ["nino", "hijo", "embrion", "concebi"],
    "bebes": ["nino", "hijo", "embrion", "concebi"],
    "fiv": ["fecund", "vitro", "procrea"],
    "vitro": ["fecund", "procrea", "embrion"],
    "fertil": ["procrea", "esteril", "fecund"],
    "inferti": ["esteril", "procrea", "fecund"],
    "embara": ["concepc", "gestac", "materni"],
    "aborto": ["abortiv", "suprimi", "vida"],
    "curar": ["terapeu", "terapia", "sanar", "enferme"],
    "curaci": ["terapeu", "terapia", "sanar", "enferme"],
    "clonac": ["clonaci", "clon"],
    "congel": ["crioco", "embrion"],
    "eutana": ["muerte", "enferme"],
    "anticon": ["contrac", "natalid"],
}


def palabras_clave(*textos: str) -> List[str]:
    vistas = []

    def agregar(r: str):
        if r and r not in vistas:
            vistas.append(r)

    for t in textos:
        for p in re.findall(r"[a-zñ]+", _normal(t or "")):
            if p != "fiv" and (len(p) < 4 or p in _VACIAS):
                continue
            r = _raiz(p)
            agregar(r)
            for extra in _SINONIMOS.get(r, []):
                agregar(extra)
    return vistas


def _parrafos(texto: str) -> List[str]:
    """Bloques del documento; los párrafos muy cortos (números, títulos) se unen al siguiente."""
    crudos = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    bloques, pendiente = [], ""
    for p in crudos:
        if len(p) < 120:
            pendiente = (pendiente + "\n" + p).strip()
            continue
        bloques.append((pendiente + "\n" + p).strip() if pendiente else p)
        pendiente = ""
    if pendiente:
        bloques.append(pendiente)
    return bloques


def pasajes_relevantes(texto: str, tema: str, indicaciones: str = "", limite: int = 40_000) -> str:
    """Devuelve el inicio del documento + los párrafos más relacionados con el tema, en su orden original.

    Si el documento ya cabe en el límite, se devuelve completo.
    """
    if not texto or len(texto) <= limite:
        return texto
    claves = palabras_clave(tema, indicaciones)
    inicio = texto[:_INICIO]
    resto = texto[_INICIO:]
    bloques = _parrafos(resto)

    def puntaje(b: str) -> float:
        n = _normal(b)
        aciertos = sum(n.count(k) for k in claves)
        distintas = sum(1 for k in claves if k in n)
        return distintas * 3 + aciertos  # premia que toque varios aspectos del tema

    puntajes = [puntaje(b) for b in bloques]
    elegidos = set()
    usado = len(inicio)
    for i in sorted(range(len(bloques)), key=lambda i: puntajes[i], reverse=True):
        if puntajes[i] <= 0:
            break
        # incluir también el párrafo anterior da contexto (suele ser el número o el subtítulo)
        for j in (i - 1, i, i + 1):
            if 0 <= j < len(bloques) and j not in elegidos:
                if usado + len(bloques[j]) > limite:
                    continue
                elegidos.add(j)
                usado += len(bloques[j]) + 6
        if usado >= limite:
            break

    if not elegidos:  # ningún párrafo menciona el tema: se usa el comienzo del documento
        return texto[:limite]

    # Si sobra espacio, se agrega más contexto alrededor de lo elegido.
    for distancia in (2, 3):
        for i in sorted(elegidos):
            for j in (i - distancia, i + distancia):
                if 0 <= j < len(bloques) and j not in elegidos and usado + len(bloques[j]) <= limite:
                    elegidos.add(j)
                    usado += len(bloques[j]) + 6

    salida, anterior = [inicio], -1
    for j in sorted(elegidos):
        if j != anterior + 1:
            salida.append("[…]")
        salida.append(bloques[j])
        anterior = j
    return "\n\n".join(salida)
