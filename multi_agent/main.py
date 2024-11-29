from datetime import datetime

from multi_agent.utils.graph import build_legal_rag_graph
from utils.state import GraphState


def main():
    graph = build_legal_rag_graph()

    initial_state = GraphState(
        chat_history=[],
        query="O que tenho de fazer para registar a minha propriedade?",
        expanded_query=[],
        metadata=[],
        code=[],
        uppercase_query="",
    )

    init_time = datetime.now()
    final_state = graph.invoke(initial_state)
    final_time = datetime.now()

    print(f"Time passed: {final_time-init_time}\n")
    # results
    print("\nExpanded Queries:", final_state["expanded_query"])
    print("\nMetadata:", final_state["metadata"])
    print("\nUppercase query:", final_state["uppercase_query"])
    print("\nCode classifier:", final_state["code"])


if __name__ == "__main__":
    main()
