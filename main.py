from workflow.podcast_flow import build_graph

def main():
    print("🕊️  Estudio Digital — Cápsulas Marianas")
    print("=" * 60)
    graph = build_graph()
    topic = ""
    while not topic.strip():
        topic = input("\n🎙️  Tema del episodio: ")
    initial_state = {
        "topic": topic, "research": None, "research_approved": False,
        "research_feedback": None, "theology_review": None, "script": None,
        "script_approved": False, "script_feedback": None, "audio_path": None,
        "current_phase": "investigacion", "revision_count": 0, "approved": False,
    }
    print("\n🚀 Iniciando producción...")
    result = graph.invoke(initial_state)
    print("\n" + "=" * 60)
    if result.get("approved"):
        print("✨ GUION FINAL:\n")
        print(result.get("script", ""))
    else:
        print("🛑 Producción detenida.")
    print("=" * 60)

if __name__ == "__main__":
    main()
