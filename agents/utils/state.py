from typing import Dict, List, Optional, TypedDict, Annotated
from langgraph.graph.message import AnyMessage, add_messages

class GraphState(TypedDict):
    chat_history: Annotated[list[AnyMessage], add_messages]
    question: str
    expanded_query: Optional[List[str]] 
    metadata: Optional[Dict]
    classification: Optional[str]
    documents: Optional[List[str]] # retrieval_results
    model_answer : Optional[str] # model answer after invoke
    next_step: str
    retries: int

class GraphConfig(TypedDict):
    max_retries: int