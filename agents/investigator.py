from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


def investigador_agent(state: dict) -> dict:
    print("📚 [Investigador] Iniciando investigación en los Archivos...")

    topic = state["topic"]

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)

    system_instruction = """
    Actúas como un Investigador Histórico y Archivero de la Santa Sede.
    Tu misión es recopilar información exacta, documentada y fiel al Magisterio para un podcast católico.

    REGLAS DE INVESTIGACIÓN:
    1. FUENTES APROBADAS: Si el tema trata sobre apariciones o revelaciones privadas, confirma si cuentan
       con la aprobación oficial de la Iglesia (Constat de supernaturalitate) o del obispo local.
    2. RIGOR HISTÓRICO: Diferencia entre "hechos históricos documentados" y "tradiciones piadosas".
    3. CITAS VERIFICABLES: Toda cita bíblica, papal o de santos debe ser real. Indica el documento de origen.
    """

    human_instruction = """
    Investiga a profundidad el siguiente tema mariano:

    TEMA: {topic}

    Estructura tu reporte así:

    ## 1. CONTEXTO HISTÓRICO Y ECLESIAL
    (Época, situación del mundo/Iglesia, y estatus de aprobación oficial si aplica).

    ## 2. HECHOS Y ACONTECIMIENTOS PRINCIPALES
    (Narra lo que ocurrió cronológicamente de forma objetiva).

    ## 3. CITAS TEXTUALES Y DOCUMENTOS
    (2 o 3 frases exactas de Santos, Papas o la Biblia, indicando autor y documento fuente).

    ## 4. NÚCLEO ESPIRITUAL
    (¿Cuál es el mensaje central para la vida de un católico hoy?).
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human", human_instruction)
    ])

    response = (prompt | llm).invoke({"topic": topic})

    print("✅ [Investigador] Investigación completada.")
    return {
        **state,
        "research": response.content,
        "current_phase": "teologia",
        "revision_count": state.get("revision_count", 0)
    }
