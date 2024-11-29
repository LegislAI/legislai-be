from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import TypedDict

from agents.classifier import code_classification_agent
from agents.lowercase import lowercase_transformation_agent
from agents.metadata import metadata_extraction_agent
from agents.query_expansion import query_expansion_agent
from agents.uppercase import uppercase_transformation_agent
from langgraph.graph import END
from langgraph.graph import START
from langgraph.graph import StateGraph
from langsmith import traceable
from utils.state import GraphState

# llm = ChatOpenAI(temperature=0)
# embeddings = OpenAIEmbeddings()
# vectorstore = Chroma(embedding_function=embeddings)
# evaluator = HallucinationEvaluator(max_retries=3)
# next_step = evaluator.evaluate(state=graph_state)


# Embedding Agent
@traceable(name="embedding")
def embedding_agent(state: GraphState) -> GraphState:
    return state


# Retrieval Agent
@traceable(name="retrieval")
def retrieval_agent(state: GraphState) -> GraphState:
    return state


@dataclass
class RAGInputs:
    original_query: str
    expanded_query: str
    classification: str
    metadata: Dict[str, Any]


class RAGOutput(TypedDict):
    embedded_query: List[float]
    retrieved_documents: List[Dict]
    relevance_scores: List[float]


@traceable(name="rag_coordinator")
def rag_coordinator_agent(state: GraphState) -> GraphState:
    """
    Coordinates and combines inputs from multiple agents for the RAG process.
    """
    # Collect and validate inputs from previous agents
    rag_inputs = RAGInputs(
        original_query=state["query"],
        expanded_query=state["expanded_query"],
        classification=state["classification"],
        metadata=state["metadata"],
    )

    rag_output = process_rag_pipeline(rag_inputs)

    # Update state with RAG results
    state["embeddings"] = rag_output["embedded_query"]
    state["retrieval_results"] = rag_output["retrieved_documents"]
    state["relevance_scores"] = rag_output["relevance_scores"]

    return state


@traceable(name="rag_pipeline")
def process_rag_pipeline(inputs: RAGInputs) -> RAGOutput:
    """
    Main RAG processing pipeline that uses inputs from multiple agents.
    """
    return inputs


def build_legal_rag_graph() -> StateGraph:
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("query_expansion", query_expansion_agent)
    workflow.add_node("code_classification", code_classification_agent)
    workflow.add_node("metadata_extraction", metadata_extraction_agent)
    workflow.add_node("uppercase_agent", uppercase_transformation_agent)
    # workflow.add_node("lowercase_agent", lowercase_transformation_agent)

    # workflow.add_node("rag_coordinator", rag_coordinator_agent)
    # # workflow.add_node("retrivel_validation", validation_agent)  # FALAR COM MALTA !!
    # workflow.add_node("prompt_engineering", prompt_engineering_agent)

    workflow.add_edge(START, "metadata_extraction")
    workflow.add_edge(START, "code_classification")
    workflow.add_edge(START, "query_expansion")

    # # Wait for all required inputs before RAG
    # workflow.add_edge("metadata_extraction", "rag_coordinator")
    # workflow.add_edge("rag_coordinator", "prompt_engineering")

    # workflow.add_conditional_edges("prompt_engineering",evaluator.evaluate())
    workflow.add_edge("query_expansion", "uppercase_agent")
    workflow.add_edge("metadata_extraction", "uppercase_agent")
    workflow.add_edge("code_classification", "uppercase_agent")
    workflow.add_edge("uppercase_agent", END)
    app = workflow.compile()
    return app
