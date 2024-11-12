from typing import List, Dict, Any
from utils.model import llm
from datetime import datetime
import json

class QueryExpansionAgent:
    def __init__(self): 
        self.init_time =  datetime.now()
        try:
            with open("examples_query_exp.json", 'r', encoding='utf-8') as file:
                self.few_shot_examples = json.load(file)
        except Exception as e:
            print(f"Error loading few-shot examples: {e}")


        self.query_expansion_prompt = """
        És um sistema de informação que processa queries dos utilizadores.
        Expande uma query dada em {{number}} queries semelhantes no seu significado.

        Estrutura:
        Segue a estrutura mostrada nos exemplos abaixo para gerar queries expandidas.

        Exemplos:
        1. Exemplo de Consulta 1: "Como funciona o processo de herança segundo a lei portuguesa?"
        Exemplo de queries Expandidas: ["Quais são os direitos dos herdeiros no processo de partilha de bens?",
                                        "Como são aplicadas as taxas de imposto sobre heranças em Portugal?"]

        2. Exemplo de Consulta 2: "Quais são as regras para o registo de uma sociedade em Portugal?"
        Exemplo de queries Expandidas: ["Quais são os tipos de sociedades que podem ser registadas em Portugal?",
                                        "Quais documentos são necessários para o registo de uma sociedade?",
                                        "Como proceder com a alteração de informações após o registo da sociedade?"

        Apenas retorna aquele número de queries expandidas.
        A tua tarefa:
        Query: "{{query}}"
        Queries Expandidas:
        """

    def run(self, query: str, number: int = 2) -> Dict[str, Any]:
        """
        Run the query expansion agent on a given query.
        """
        try:
            formatted_prompt = self.query_expansion_prompt.replace(
                "{{query}}", query
            ).replace("{{number}}", str(number))
            
            messages = self.few_shot_examples + [{"role": "user", "content": formatted_prompt}]
            response = llm.invoke(messages)
            
            # Process the response to ensure it's in the correct format
            # expanded_queries = self._process_response(response)
            
            return {
                "expanded_queries": response,
                "success": True
            }
            
        except Exception as e:
            print(f"Error in query expansion: {e}")
            return {
                "expanded_queries": [query],  # Return original query if expansion fails
                "success": False,
                "error": str(e)
            }

    def _process_response(self, response: str) -> List[str]:
        """
        Process the LLM response to extract expanded queries.
        """
        try:
            # Clean up the response and extract queries
            queries = response.strip().split('\n')
            # Remove any empty queries and clean up formatting
            queries = [q.strip() for q in queries if q.strip()]
            return queries
        except Exception as e:
            print(f"Error processing response: {e}")
            return []

def query_expansion_agent(state):
    agent = QueryExpansionAgent()
    result = agent.run(state['query'])
    last_time = datetime.now()
    print("time passed in QUERY EXPANSION\n", last_time - agent.init_time)
    state['expanded_query'] = [result["expanded_queries"]]
    return state

