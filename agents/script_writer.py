from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


def guionista_agent(state: dict) -> dict:
    print("✍️ [Guionista] Redactando la Cápsula Mariana...")

    research = state.get("research", "")
    feedback = state.get("script_feedback", "")  # Si hubo rechazo previo, toma el feedback

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)

    system_instruction = """
    Eres el Guionista de un podcast católico mariano en formato "Cápsula Breve".
    Transformas investigación teológica en guiones de audio dinámicos, profundos y directos al corazón.

    REGLAS DEL GUION:
    1. EXTENSIÓN: Entre 300 y 400 palabras (exactamente 2.5 minutos de locución).
    2. RITMO: El gancho inicial debe captar la atención en los primeros 3 segundos.
    3. FIDELIDAD: Basate ÚNICAMENTE en la investigación proporcionada.
    4. MARCADORES DE AUDIO: Usa [MÚSICA: descripción], [PAUSA CORTA], [ÉNFASIS].
    5. ESTILO BOCA-A-OÍDO: Frases cortas, como contarle una historia a un amigo.
    """

    human_instruction = """
    Crea el guion usando esta investigación aprobada:

    INVESTIGACIÓN BASE:
    {research}

    {feedback_section}

    ESTRUCTURA OBLIGATORIA (300-400 palabras):

    [MÚSICA: Gancho inspirador]
    1. EL GANCHO (15 seg): Una pregunta intrigante o dato asombroso.
    2. LA HISTORIA (1 min): ¿Qué pasó? ¿Dónde? ¿Cuándo? La esencia del evento.
    [PAUSA CORTA]
    3. EL NÚCLEO ESPIRITUAL (45 seg): La pepita de oro teológica. ¿Qué nos pide la Virgen?
    [MÚSICA: Suave y contemplativa]
    4. DESPEDIDA Y ORACIÓN (30 seg): Cierre + mini-oración ("Madre, enséñanos a...").
    """

    feedback_section = f"FEEDBACK DE LA DIRECTORA EDITORIAL:\n{feedback}" if feedback else ""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human", human_instruction)
    ])

    response = (prompt | llm).invoke({
        "research": research,
        "feedback_section": feedback_section
    })

    revision_count = state.get("revision_count", 0)

    print("✅ [Guionista] Guion generado. Listo para revisión editorial.")

    # ✅ FIX 3: Return explícito del estado actualizado
    return {
        **state,
        "script": response.content,
        "current_phase": "audio",
        "revision_count": revision_count + 1
    }
