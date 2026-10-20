"""Censor Doctrinal: revisa la investigación Y el guion final contra el texto oficial
(uno o varios documentos combinados)."""
import re
from typing import List

from pydantic import BaseModel, Field

from agents import llm

VEREDICTOS = ("APROBADO", "CORREGIR", "RECHAZADO")


class RevisionDoctrinal(BaseModel):
    veredicto: str = Field(description="Exactamente uno de: APROBADO, CORREGIR, RECHAZADO")
    nivel_rigor: int = Field(description="Rigor doctrinal e histórico del 1 al 10")
    citas_verificadas: List[str] = Field(description="Citas que coinciden con el texto oficial")
    citas_dudosas: List[str] = Field(description="Citas que no aparecen, están alteradas o se atribuyen al documento equivocado")
    afirmaciones_a_corregir: List[str] = Field(description="Frases doctrinalmente imprecisas, con la corrección propuesta")
    tono_pastoral: str = Field(description="Evaluación del tono: ¿acoge a quien sufre infertilidad sin juzgar?")
    observaciones: List[str] = Field(description="Sugerencias concretas de mejora")


SISTEMA = """
Eres el Censor Doctrinal del podcast católico «La maternidad no siempre tiene cuna; a veces tiene cruz».
Auditas textos frente al Magisterio de la Iglesia católica y, cuando se te entrega, frente al TEXTO OFICIAL del documento.
Sé exigente con las citas: si una cita textual no aparece en el texto oficial, va en citas_dudosas.
Si el texto oficial trae VARIOS documentos (separados por === DOCUMENTO ===), verifica cada cita contra el documento
que dice citar: una cita atribuida al documento equivocado también va en citas_dudosas, indicando a cuál pertenece.
Si se afirma que la enseñanza cambió o evolucionó entre documentos, comprueba que los textos lo respalden.
Criterio de veredicto:
- APROBADO: sin errores doctrinales y sin citas dudosas.
- CORREGIR: errores menores, citas dudosas o tono mejorable.
- RECHAZADO: contradice la doctrina católica o confunde gravemente al oyente.
"""


def _clave(texto: str) -> str:
    t = texto.lower().replace("…", " ").replace("...", " ")
    t = re.sub(r"[«»\"“”'‘’]", "", t)
    return re.sub(r"\s+", " ", t).strip(" .,;:-")


def sin_duplicados(items: List[str]) -> List[str]:
    """Quita repetidas y versiones recortadas («…») de una cita que ya aparece completa."""
    candidatos = sorted({i.strip() for i in items if i and i.strip()}, key=len, reverse=True)
    elegidos, claves = [], []
    for item in candidatos:
        clave = _clave(item)
        # una versión recortada puede tener varios trozos separados por «…»
        trozos = [_clave(t) for t in re.split(r"…|\.\.\.", item) if len(_clave(t)) > 12] or [clave]
        if any(all(tr in k for tr in trozos) for k in claves):
            continue
        elegidos.append(item)
        claves.append(clave)
    orden = {i.strip(): n for n, i in enumerate(items) if i}
    return sorted(elegidos, key=lambda x: orden.get(x, 0))


def revisar(contenido: str, tipo: str = "investigación", fuente_texto: str = "") -> RevisionDoctrinal:
    pedido = ""
    if fuente_texto:
        pedido += f"TEXTO OFICIAL DE REFERENCIA:\n<<<\n{fuente_texto}\n>>>\n\n"
    pedido += f"{tipo.upper()} A REVISAR:\n<<<\n{contenido}\n>>>\n\nEntrega la revisión doctrinal."
    revision = llm.estructurado(pedido, RevisionDoctrinal, sistema=SISTEMA, temperatura=0.1)
    revision.citas_verificadas = sin_duplicados(revision.citas_verificadas)
    revision.citas_dudosas = sin_duplicados(revision.citas_dudosas)
    revision.afirmaciones_a_corregir = sin_duplicados(revision.afirmaciones_a_corregir)
    revision.observaciones = sin_duplicados(revision.observaciones)
    veredicto = revision.veredicto.strip().upper()
    revision.veredicto = veredicto if veredicto in VEREDICTOS else "CORREGIR"
    if revision.citas_dudosas and revision.veredicto == "APROBADO":
        revision.veredicto = "CORREGIR"
    return revision


def resumen_para_correccion(revision: RevisionDoctrinal) -> str:
    partes = []
    if revision.citas_dudosas:
        partes.append("Citas dudosas (quitar o corregir con el texto exacto):\n- " + "\n- ".join(revision.citas_dudosas))
    if revision.afirmaciones_a_corregir:
        partes.append("Afirmaciones a corregir:\n- " + "\n- ".join(revision.afirmaciones_a_corregir))
    if revision.observaciones:
        partes.append("Observaciones:\n- " + "\n- ".join(revision.observaciones))
    if revision.tono_pastoral:
        partes.append(f"Tono pastoral: {revision.tono_pastoral}")
    return "\n\n".join(partes)
