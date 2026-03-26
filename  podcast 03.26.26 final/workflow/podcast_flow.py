from langgraph.graph import StateGraph, END
from workflow.state import PodcastState
from agents.investigator import investigador_agent
from agents.theologian import teologo_agent
from agents.script_writer import guionista_agent
from agents.publisher import publisher_agent


def revision_teologica_node(state: PodcastState) -> dict:
    print("⛪ [Nodo] Censor Doctrinal...")
    return teologo_agent(state)


def approval_node(state: PodcastState) -> dict:
    print("\n" + "=" * 60)
    print("📜 INVESTIGACIÓN")
    print("=" * 60)
    print(state.get("research", ""))
    review = state.get("theology_review")
    if review:
        print(f"\n⛪ VEREDICTO: {review.veredicto} | Rigor: {review.nivel_rigor}/10")
        for obs in review.observaciones:
            print(f"  • {obs}")
    print("=" * 60)
    decision = input("\n👑 DIRECTORA: ¿Apruebas continuar al guion? (si/no): ")
    approved = decision.strip().lower() == "si"
    return {**state, "approved": approved}


def route_after_approval(state)  -> str:
    return "writer" if state.get("approved") else END

def route_after_theology(state) -> str:
    review = state.get("theology_review")
    if review and review.veredicto == "RECHAZADO":
        return END
    return "approval"

def route_after_writer(state) -> str:
    return "publisher" if state.get("audio_path") else END


def build_graph():
    print("⚙️ Construyendo motor de agentes...")
    graph = StateGraph(PodcastState)

    graph.add_node("investigator", investigador_agent)
    graph.add_node("theologian",   revision_teologica_node)
    graph.add_node("approval",     approval_node)
    graph.add_node("writer",       guionista_agent)
    graph.add_node("publisher",    publisher_agent)

    graph.set_entry_point("investigator")
    graph.add_edge("investigator", "theologian")
    graph.add_conditional_edges("theologian", route_after_theology)
    graph.add_conditional_edges("approval",   route_after_approval)
    graph.add_conditional_edges("writer",     route_after_writer)
    graph.add_edge("publisher", END)

    return graph.compile()
