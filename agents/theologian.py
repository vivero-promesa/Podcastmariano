from typing import List
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

class QualityChecklist(BaseModel):
    veredicto: str = Field(description="'APROBADO', 'CORREGIR' o 'RECHAZADO'")
    cita_catecismo: str = Field(description="Referencia al CIC o Magisterio.")
    contexto_historico: str = Field(description="Validación de hechos y fechas.")
    nivel_rigor: int = Field(description="Escala del 1 al 10.")
    observaciones: List[str] = Field(description="Sugerencias de ajuste.")

def teologo_agent(state: dict) -> dict:
    print("⛪ [Teólogo] Iniciando revisión doctrinal...")
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-001", temperature=0)
    structured_llm = llm.with_structured_output(QualityChecklist)
    
    investigacion = state.get("research", "No hay investigación disponible.")
    
    prompt = f"""
    Eres el Censor Doctrinal de 'Cápsulas Marianas'.
    Tu misión es auditar la INVESTIGACIÓN histórica y teológica frente a la Tradición
    y el Magisterio de la Iglesia Católica.

    INVESTIGACIÓN A REVISAR:
    {investigacion}

    Genera el checklist de calidad con veredicto ('APROBADO', 'CORREGIR' o 'RECHAZADO'),
    referencias al Catecismo, validación histórica, nivel de rigor (1-10) y observaciones.
    """
    
    resultado = structured_llm.invoke(prompt)
    
    print(f"✅ [Teólogo] Veredicto: {resultado.veredicto} | Rigor: {resultado.nivel_rigor}/10")
    
    return {
        **state,
        "theology_review": resultado,
        "current_phase": "guion"
    }
