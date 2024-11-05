import os
import json
from dotenv import load_dotenv
from langchain_together import Together
from prompt_toolkit import prompt

load_dotenv()


class QueryExpander:
    def __init__(self):
        self.query_expansion_prompt = """
        You are part of an information system that processes users queries.
        You expand a given query into {{number}} queries that are similar in meaning.

        Structure:
        Follow the structure shown below in examples to generate expanded queries.
        Examples:
        1. Example Query 1: "climate change effects"
        Example Expanded Queries: ["impact of climate change", "consequences of global warming", "effects of environmental changes"]

        2. Example Query 2: ""machine learning algorithms""
        Example Expanded Queries: ["neural networks", "clustering", "supervised learning", "deep learning"]

        Your Task:
        Query: "{{query}}"
        Example Expanded Queries:
        """
        self.llm = Together(
            model="mistralai/Mistral-7B-Instruct-v0.1",
            together_api_key=os.getenv("TOGETHER_API_KEY"),
            max_tokens=256,
        )

    def expand_query(self, query: str, number: int = 5):
        formatted_prompt = self.query_expansion_prompt.replace(
            "{{query}}", query
        ).replace("{{number}}", str(number))
        response = self.llm.invoke(formatted_prompt)

        try:
            expanded_queries = response
        except json.JSONDecodeError:
            expanded_queries = query

        return {"queries": expanded_queries}


if __name__ == "__main__":
    user_query = prompt("Escreve a query: ")
    expansion_number = int(
        prompt("Escreve o número de queries expandidas que desejas: ")
    )
    expander = QueryExpander()
    result = expander.expand_query(query=user_query, number=expansion_number)
    print("Queries expandidas:", result["queries"])
