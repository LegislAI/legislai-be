from datetime import datetime
from typing import Any
from typing import Dict


class UppercaseTransformationAgent:
    def run(self, query: str) -> Dict[str, Any]:
        """
        Run the uppercase transformation agent on a given query.
        """
        try:
            transformed_query = self._transform_to_uppercase(query)
            return transformed_query
        except Exception as e:
            print(f"Error transforming query: {e}")
            return self._get_default_response(query)

    def _transform_to_uppercase(self, text: str) -> str:
        """
        Transform the input text to uppercase.
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
        return text.upper()

    def _get_default_response(self, query: str) -> Dict[str, Any]:
        """
        Return default response when transformation fails.
        """
        return query


def uppercase_transformation_agent(state: Dict[str, Any]) -> Dict[str, Any]:

    agent = UppercaseTransformationAgent()
    transformation_result = agent.run(state["query"])

    # Update the state with the transformation results
    state["uppercase_query"] = transformation_result
    return state
