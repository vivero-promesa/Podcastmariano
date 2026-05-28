from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

def guionista_agent(state: dict) -> dict:
    print("✍️ [Guionista] Diseñando arquitectura del guion (Fórmula Spotify)...")

    research = state.get("research", "")
    feedback = state.get("script_feedback", "")

    # Mantenemos el modelo estable y subimos un poco la temperatura a 0.7 
    # para darle más creatividad narrativa en el storytelling.
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

    system_instruction = """
    Eres un Productor y Guionista de nivel 'Top 10 Spotify', experto en retención de audiencia.
    Tu especialidad es escribir sobre el cruce entre bioética, fe, historia e Inteligencia Artificial.
    Transformas investigaciones profundas en guiones de podcast adictivos, utilizando técnicas de neuro-storytelling.

    REGLAS DE INGENIERÍA DE GUION:
    1. ESTILO: Habla como si le estuvieras contando un secreto fascinante a un amigo inteligente. NADA de lenguaje académico aburrido.
    2. MARCADORES SONOROS: Actúa como director de audio. Inserta directivas precisas en corchetes: [SFX: Latido de corazón], [MÚSICA: Tensión in crescendo], [PAUSA 2s].
    3. RITMO: Frases cortas, contundentes. Diseñadas para ser leídas en voz alta sin ahogarse.
    4. TONO: Mantén un balance perfecto entre el misterio, la profundidad filosófica/teológica y el dilema moral contemporáneo.
    """

    human_instruction = """
    Utiliza esta investigación validada y el feedback para generar el episodio.

    [INVESTIGACIÓN BASE]:
    {research}

    {feedback_section}

    Aplica ESTRICTAMENTE la siguiente "Fórmula de Retención Spotify" en este orden exacto. Subtitula cada sección en el guion final pero de forma invisible para el locutor (ej. --- HOOK ---).

    1. HOOK (30 seg): [MÚSICA: Intrigante]. Lanza un dato perturbador, una paradoja o una pregunta que rompa la mente del oyente en los primeros 5 segundos.
    2. HISTORIA IMPACTANTE: Aterriza el hook en una historia humana real o un evento documentado en la investigación.
    3. PREGUNTA CENTRAL: Plantea el dilema ético/teológico de fondo ("¿Hasta dónde podemos llegar...?").
    4. CONFLICTO: Muestra los dos lados de la moneda (ej. el avance vs. el límite moral/divino).
    5. EXPLICACIÓN SENCILLA: Traduce la teología o la ciencia compleja a palabras de a pie, usando una metáfora visual.
    6. EJEMPLOS REALES: Da una aplicación práctica que el oyente viva hoy en su celular o en su vida diaria.
    7. GIRO INESPERADO: [MÚSICA: Cambio drástico]. Revela algo que la investigación dice que nadie se espera. Un cambio total de perspectiva.
    8. CONCLUSIÓN EMOCIONAL: Conecta el tema con el corazón humano, la fe y la esperanza.
    9. PREGUNTA FINAL: Cierra con un interrogante abierto y profundo que deje al oyente pensando todo el día. [SFX: Eco sutil, corte a negro].
    """

    feedback_section = f"[FEEDBACK DE DIRECCIÓN]:\n{feedback}" if feedback else ""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human", human_instruction)
    ])

    response = (prompt | llm).invoke({
        "research": research,
        "feedback_section": feedback_section
    })

    revision_count = state.get("revision_count", 0)

    print("✅ [Guionista] Guion generado con estructura de alta retención.")

    return {
        **state,
        "script": response.content,
        "current_phase": "audio",
        "revision_count": revision_count + 1
    }
