import operator
from typing import Annotated
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import TypedDict

from langgraph.graph.message import add_messages
from langgraph.graph.message import AnyMessage


class GraphState(TypedDict):
    chat_history: Annotated[list[AnyMessage], add_messages]
    query: Annotated[str, operator.add]
    metadata: Annotated[List[Dict], operator.add]
    code: Annotated[List[Dict], operator.add]
    expanded_query: Annotated[List[Dict], operator.add]
    # documents: Optional[List[str]] # retrieval_results
    # model_answer : Optional[str] # model answer after invoke
    uppercase_query: Annotated[str, operator.add]


class GraphConfig(TypedDict):
    max_retries: int
