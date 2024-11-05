from typing import Dict, List, Optional, TypedDict, Any
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langsmith import traceable
from dataclasses import dataclass
import numpy as np
from utils.state import GraphState
from services.agents.hallucination import HallucinationEvaluator

llm = ChatOpenAI(temperature=0)
embeddings = OpenAIEmbeddings()
vectorstore = Chroma(embedding_function=embeddings)
evaluator = HallucinationEvaluator(max_retries=3)
next_step = evaluator.evaluate(state=graph_state)

@traceable(name="query_expansion")
def query_expansion_agent(state: GraphState) -> GraphState:
    return state

# Classification Agent
@traceable(name="classification")
def classification_agent(state: GraphState) -> GraphState:
    return state

# Metadata Extraction Agent
@traceable(name="metadata_extraction")
def metadata_extraction_agent(state: GraphState) -> GraphState:
    return state

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
        metadata=state["metadata"]
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


# Update the graph structure
def build_legal_rag_graph() -> StateGraph:
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("query_expansion", query_expansion_agent)
    workflow.add_node("classification", classification_agent)
    workflow.add_node("metadata_extraction", metadata_extraction_agent)
    workflow.add_node("rag_coordinator", rag_coordinator_agent)
    # workflow.add_node("retrivel_validation", validation_agent)  # FALAR COM MALTA !!
    workflow.add_node("prompt_engineering", prompt_engineering_agent)
    

    workflow.set_entry_point("classification")
    workflow.add_edge("classification", "query_expansion")
    workflow.add_edge("classification", "metadata_extraction")
    
    # Wait for all required inputs before RAG
    workflow.add_edge("metadata_extraction", "rag_coordinator")
    
    workflow.add_edge("rag_coordinator", "prompt_engineering")

    workflow.add_conditional_edges("prompt_engineering",evaluator.evaluate())
    workflow.add_edge("prompt_engineering", END)
    
    return workflow

