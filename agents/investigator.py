"""Agente Investigador: arma el informe del episodio a partir de uno o varios documentos oficiales."""
from typing import List, Optional

import config
from agents import llm
from agents.fuentes import texto_oficial

# Tope del texto oficial que se envía a Gemini cuando se combinan documentos (~150 mil tokens).
LIMITE_TOTAL = 600_000

SISTEMA = f"""
Eres la investigadora del podcast católico «{config.PODCAST['nombre']}».
Audiencia: {config.PODCAST['audiencia']}. Muchas oyentes viven infertilidad, pérdidas o tratamientos:
habla con verdad y con ternura, nunca con condena.

REGLAS:
1. Fidelidad al Magisterio de la Iglesia católica.
2. Cuando recibas el TEXTO OFICIAL del documento, toda cita textual debe copiarse EXACTA de ese texto,
con su número o párrafo (ej.: «...» (Donum Vitae, II, B, 5)). Si algo no está en el texto, no lo cites.
3. Si recibes VARIOS documentos (separados por === DOCUMENTO ===), cada cita debe indicar de qué documento
sale y copiarse exacta de ese documento, nunca de otro.
4. Separa hechos documentados de opiniones. Marca con [VERIFICAR] cualquier dato que no venga del texto oficial.
5. Escribe en español claro, sin latín innecesario.
"""

ESTRUCTURA = """
Estructura el informe en Markdown, con estas secciones:

## 1. El documento en 3 frases
(Qué es, quién lo escribió, cuándo y por qué.)

## 2. Cinco enseñanzas clave
(Para cada una: explicación sencilla + cita textual exacta con su número.)
{evolucion}
## 3. Lo que la gente realmente pregunta
(5 preguntas tal como se escriben en Google o TikTok — por ejemplo «¿la FIV es pecado?» — y qué responde el documento.)

## 4. Historias humanas y datos
(Casos reales o datos científicos que ayuden a aterrizar el tema. Marca con [VERIFICAR] lo que no salga del documento.)

## 5. Lo que casi nadie sabe
(Un dato o matiz sorprendente del documento que sirva de giro en el episodio.)

## 6. Esperanza para quien escucha
(Mensaje pastoral para parejas con infertilidad o heridas, apoyado en el documento.)
"""

EVOLUCION = """
## 2b. Cómo evolucionó la enseñanza
(Recorre los documentos en orden cronológico: qué afirma cada uno, qué precisa, amplía o aplica el posterior,
y qué se mantiene igual. Cita cada documento con su nombre y número.)
"""


def _documentos(documento: Optional[dict], documentos: Optional[List[dict]]) -> List[dict]:
    lista = documentos if documentos is not None else ([documento] if documento else [])
    return [d for d in lista if d and d.get("clave") != "LIBRE"]


def investigar(
    tema: str,
    documento: Optional[dict] = None,
    indicaciones: str = "",
    correcciones: str = "",
    informe_anterior: str = "",
    documentos: Optional[List[dict]] = None,
) -> dict:
    """Investiga a partir de un documento (documento=...) o de varios combinados (documentos=[...])."""
    docs = _documentos(documento, documentos)
    con_url = [d for d in docs if d.get("url")]
    tope = LIMITE_TOTAL // max(1, len(con_url))

    partes, urls, errores, sin_texto = [], [], [], []
    for d in docs:
        if not d.get("url"):
            sin_texto.append(d["titulo"])
            continue
        try:
            texto = texto_oficial(d["url"])[:tope]
            partes.append(f"=== DOCUMENTO: {config.etiqueta_documento(d)} — {d['url']} ===\n{texto}")
            urls.append(d["url"])
        except Exception as e:  # sin internet o vatican.va caído: seguimos con búsqueda web
            errores.append(f"{d['titulo']}: {e}")
            sin_texto.append(d["titulo"])
    fuente = "\n\n".join(partes)

    titulos = " + ".join(config.etiqueta_documento(d) for d in docs) if docs else "Tema libre"
    pedido = f"TEMA DEL EPISODIO: {tema}\nDOCUMENTO(S) BASE: {titulos}\n"
    if indicaciones:
        pedido += f"\nINDICACIONES DE LA DIRECTORA:\n{indicaciones}\n"
    pedido += ESTRUCTURA.format(evolucion=EVOLUCION if len(docs) > 1 else "")
    if correcciones and informe_anterior:
        pedido += (
            "\nREESCRIBE el informe anterior aplicando TODAS las correcciones del Censor Doctrinal. "
            "Quita o corrige cada cita dudosa con el texto exacto del documento y conserva lo que ya estaba bien.\n\n"
            f"INFORME ANTERIOR:\n<<<\n{informe_anterior}\n>>>\n\nCORRECCIONES DEL CENSOR:\n{correcciones}\n"
        )

    if fuente:
        if sin_texto:
            pedido += (
                f"\nNo tienes el texto oficial de: {', '.join(sin_texto)}. "
                "Toda cita de esos documentos va marcada con [VERIFICAR]."
            )
        pedido = f"TEXTO OFICIAL DEL DOCUMENTO O DOCUMENTOS:\n<<<\n{fuente}\n>>>\n\n" + pedido
        informe = llm.texto(pedido, sistema=SISTEMA, temperatura=0.3)
    else:
        pedido += "\nNo tienes el texto oficial: usa la búsqueda web y marca con [VERIFICAR] toda cita."
        informe = llm.texto(pedido, sistema=SISTEMA, temperatura=0.3, buscar_web=True)

    return {
        "informe": informe,
        "fuente_url": " · ".join(urls),
        "fuente_texto": fuente,
        "con_fuente_oficial": bool(fuente) and not sin_texto,
        "error_fuente": "; ".join(errores) or (f"Sin texto oficial: {', '.join(sin_texto)}" if sin_texto else ""),
        "documentos": [d["clave"] for d in docs],
    }
