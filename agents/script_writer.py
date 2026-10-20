"""Agente Guionista: convierte la investigación aprobada en un guion de 15-20 minutos
para grabar con tu voz, con «momentos clip» listos para TikTok e Instagram."""
from typing import Optional

import config
from agents import llm

PALABRAS_POR_MINUTO = 140

SISTEMA = f"""
Eres la guionista de «{config.PODCAST['nombre']}», un podcast católico de bioética.
Audiencia: {config.PODCAST['audiencia']}.
Escribes para el oído: como si le contaras algo importante a una amiga inteligente, con calidez y sin tono académico.

REGLAS:
1. Usa SOLO las citas que trae la investigación, copiadas exactas y con su número. No inventes citas ni datos.
2. Frases cortas, fáciles de leer en voz alta.
3. Indicaciones de producción entre corchetes: [MÚSICA: ...], [PAUSA 2s], [SFX: ...]. Nunca se leen.
4. Verdad con ternura: nunca condenar a quien pasó por FIV, pérdidas o infertilidad.
5. Usa al menos 2 veces, de forma natural, las palabras que la gente busca: {", ".join(config.PALABRAS_BUSQUEDA[:6])}.
"""

FORMULA = """
Sigue esta fórmula, en este orden. Marca cada sección con una línea tipo «--- HOOK ---» (no se lee).

1. HOOK (primeros 30 s): una pregunta o dato que detenga el scroll, usando una palabra de búsqueda (ej.: «¿La FIV es pecado?»).
2. PRESENTACIÓN (15 s): «Bienvenida a La maternidad no siempre tiene cuna…» y de qué trata hoy.
3. HISTORIA: una historia humana real o documentada de la investigación.
4. PREGUNTA CENTRAL: el dilema de fondo.
5. LO QUE DICE LA IGLESIA: las enseñanzas clave con sus citas exactas, explicadas con metáforas sencillas.
6. LLAMADO A MITAD: «Si esto te está sirviendo, síguenos en Spotify y compártelo con alguien que lo necesite.»
7. LA VIDA REAL: aplicaciones concretas para la vida diaria y para parejas con infertilidad.
8. GIRO: lo que casi nadie sabe.
9. CIERRE CON ESPERANZA: conexión con la fe y el corazón.
10. PREGUNTA FINAL + DESPEDIDA: invita a comentar, seguir el programa e ir a Instagram y TikTok {redes}.

MOMENTOS CLIP: marca con [CLIP] al inicio y [/CLIP] al final 5 fragmentos de 30 a 60 segundos
(70 a 140 palabras) que se entiendan solos, sin contexto, y que funcionen como video viral.
"""


def escribir_guion(
    investigacion: str,
    tema: str,
    duracion_min: int = 18,
    indicaciones: str = "",
    correcciones: str = "",
    guion_anterior: Optional[str] = None,
) -> str:
    palabras = duracion_min * PALABRAS_POR_MINUTO
    pedido = f"TEMA: {tema}\nDURACIÓN OBJETIVO: {duracion_min} minutos (unas {palabras} palabras).\n\n"
    pedido += f"INVESTIGACIÓN APROBADA:\n<<<\n{investigacion}\n>>>\n"
    pedido += FORMULA.format(redes=config.PODCAST["instagram"])
    if indicaciones:
        pedido += f"\nINDICACIONES DE LA DIRECTORA:\n{indicaciones}\n"
    if correcciones and guion_anterior:
        pedido += (
            "\nREESCRIBE este guion aplicando TODAS las correcciones del Censor Doctrinal, "
            f"manteniendo lo que ya funciona.\n\nGUION ANTERIOR:\n<<<\n{guion_anterior}\n>>>\n\n"
            f"CORRECCIONES DEL CENSOR:\n{correcciones}\n"
        )
    return llm.texto(pedido, sistema=SISTEMA, temperatura=0.7)
