"""Agente Investigador: arma el informe del episodio a partir del documento oficial."""
from typing import Optional

import config
from agents import llm
from agents.fuentes import texto_oficial

SISTEMA = f"""
Eres la investigadora del podcast católico «{config.PODCAST['nombre']}».
Audiencia: {config.PODCAST['audiencia']}. Muchas oyentes viven infertilidad, pérdidas o tratamientos:
habla con verdad y con ternura, nunca con condena.

REGLAS:
1. Fidelidad al Magisterio de la Iglesia católica.
2. Cuando recibas el TEXTO OFICIAL del documento, toda cita textual debe copiarse EXACTA de ese texto,
   con su número o párrafo (ej.: «...» (Donum Vitae, II, B, 5)). Si algo no está en el texto, no lo cites.
3. Separa hechos documentados de opiniones. Marca con [VERIFICAR] cualquier dato que no venga del texto oficial.
4. Escribe en español claro, sin latín innecesario.
"""

ESTRUCTURA = """
Estructura el informe en Markdown, con estas secciones:

## 1. El documento en 3 frases
(Qué es, quién lo escribió, cuándo y por qué.)

## 2. Cinco enseñanzas clave
(Para cada una: explicación sencilla + cita textual exacta con su número.)

## 3. Lo que la gente realmente pregunta
(5 preguntas tal como se escriben en Google o TikTok — por ejemplo «¿la FIV es pecado?» — y qué responde el documento.)

## 4. Historias humanas y datos
(Casos reales o datos científicos que ayuden a aterrizar el tema. Marca con [VERIFICAR] lo que no salga del documento.)

## 5. Lo que casi nadie sabe
(Un dato o matiz sorprendente del documento que sirva de giro en el episodio.)

## 6. Esperanza para quien escucha
(Mensaje pastoral para parejas con infertilidad o heridas, apoyado en el documento.)
"""


def investigar(tema: str, documento: Optional[dict] = None, indicaciones: str = "") -> dict:
    url = (documento or {}).get("url", "")
    fuente = ""
    error_fuente = ""
    if url:
        try:
            fuente = texto_oficial(url)
        except Exception as e:  # sin internet o vatican.va caído: seguimos con búsqueda web
            error_fuente = str(e)

    titulo_doc = config.etiqueta_documento(documento) if documento else "Tema libre"
    pedido = f"TEMA DEL EPISODIO: {tema}\nDOCUMENTO BASE: {titulo_doc}\n"
    if indicaciones:
        pedido += f"\nINDICACIONES DE LA DIRECTORA:\n{indicaciones}\n"
    pedido += ESTRUCTURA

    if fuente:
        pedido = f"TEXTO OFICIAL DEL DOCUMENTO (fuente: {url}):\n<<<\n{fuente}\n>>>\n\n" + pedido
        informe = llm.texto(pedido, sistema=SISTEMA, temperatura=0.3)
    else:
        pedido += "\nNo tienes el texto oficial: usa la búsqueda web y marca con [VERIFICAR] toda cita."
        informe = llm.texto(pedido, sistema=SISTEMA, temperatura=0.3, buscar_web=True)

    return {
        "informe": informe,
        "fuente_url": url,
        "fuente_texto": fuente,
        "con_fuente_oficial": bool(fuente),
        "error_fuente": error_fuente,
    }
