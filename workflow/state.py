from typing import TypedDict, Optional, List
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Modelo estructurado para el Censor Teológico
# ─────────────────────────────────────────────
class QualityChecklist(BaseModel):
    veredicto: str = Field(description="'APROBADO', 'CORREGIR' o 'RECHAZADO'")
    cita_catecismo: str = Field(description="Referencia al CIC o Magisterio.")
    contexto_historico: str = Field(description="Validación de hechos y fechas.")
    nivel_rigor: int = Field(description="Escala del 1 al 10.")
    observaciones: List[str] = Field(description="Sugerencias de ajuste.")


# ─────────────────────────────────────────────
# Estado unificado del Podcast
# ─────────────────────────────────────────────
class PodcastState(TypedDict):
    # 1. Entrada
    topic: str

    # 2. Investigación
    research: Optional[str]
    research_approved: bool
    research_feedback: Optional[str]

    # 3. Revisión Teológica
    theology_review: Optional[QualityChecklist]

    # 4. Guion
    script: Optional[str]
    script_approved: bool
    script_feedback: Optional[str]

    # 5. Audio
    audio_path: Optional[str]

    # 6. Control del sistema
    current_phase: str          # "investigacion" | "teologia" | "guion" | "audio" | "completado"
    revision_count: int         # Evita bucles infinitos (máx. 3 revisiones)
    approved: bool              # Guardrail humano final
