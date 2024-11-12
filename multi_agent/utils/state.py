from typing import Dict, List, Optional, TypedDict, Annotated, Any
from langgraph.graph.message import AnyMessage, add_messages
import operator

class GraphState(TypedDict):
    chat_history: Annotated[list[AnyMessage], add_messages]
    query: Annotated[str, operator.add]
    metadata: Annotated[List[Dict], operator.add]
    code: Annotated[List[Dict], operator.add]
    expanded_query: Annotated[List[Dict], operator.add]
    # documents: Optional[List[str]] # retrieval_results
    # model_answer : Optional[str] # model answer after invoke
    uppercase_query : Annotated[str, operator.add]
    

class GraphConfig(TypedDict):
    max_retries: int