from typing import Dict, Any
from time import perf_counter

class EchoAgent:
    """
    A agent that returns the input query.
    """
    
    def run(self, query: str) -> Dict[str, Any]:
        """
        Returns the query with minimal processing overhead.
        """
        
        # result = {
        #     'query': query
        # }
        
        return query

def echo_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = EchoAgent()
    state['query'] = agent.run(state['query'])
    print(type(state['query']))
    return state