import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from together import Together

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.getenv("API_KEY")

data_atual = datetime.now()
data_formatada = data_atual.strftime("%Y-%m-%d")


class Preprocessing:
    def __init__(self):
        with open("bin/query_expansion_few_show_examples.json") as f:
            self.query_expansion_few_shot_examples = json.load(f)

        with open("bin/query_metadata_few_shot_examples.json") as f:
            self.query_metadata_few_shot_examples = json.load(f)

        self.client = Together(api_key=API_KEY)

    def query_enhancement(self, query: str) -> str:
        query_expansion_prompt = f"""
        És um sistema de informação que processa queries dos utilizadores.
        Expande uma query dada em 4 queries semelhantes no seu significado.

        Estrutura:
        Segue a estrutura mostrada nos exemplos abaixo para gerar queries expandidas.

        Exemplos:

            Exemplo 1:
                Query: "Como funciona o processo de herança segundo a lei portuguesa?"
                Queries Expandidas: ["Quais são os direitos dos herdeiros no processo de partilha de bens?",
                                      "Como são aplicadas as taxas de imposto sobre heranças em Portugal?",
                                      "Quais são os prazos e condições para a aceitação ou renúncia à herança?",
                                      "Como se define a herança legítima e a herança testamentária na legislação?"]

            Exemplo 2:
                Query: "Quais são as regras para o registo de uma sociedade em Portugal?"
                Queries Expandidas: ["Quais são os tipos de sociedades que podem ser registadas em Portugal?",
                                      "Quais documentos são necessários para o registo de uma sociedade?",
                                      "Como proceder com a alteração de informações após o registo da sociedade?",
                                      "Quais são os prazos legais para o registo de uma sociedade após sua constituição?"]

        A tua tarefa:
            Query: "{query}"
            Queries Expandidas:
        """
        return query_expansion_prompt

    def _expand_query(self, query: str, few_shot_examples: list) -> dict:
        try:
            messages = few_shot_examples + [{"role": "user", "content": query}]
            init_time = datetime.now()

            response = self.client.chat.completions.create(
                model="meta-llama/Llama-Vision-Free",
                messages=messages,
            )
            final_time = datetime.now()
            LOG.info(f"Query expansion took {final_time - init_time} seconds")

            expanded_queries = response
        except json.JSONDecodeError:
            LOG.error("Failed to decode JSON response for query expansion.")
            expanded_queries = query
        finally:
            return {"queries": expanded_queries}

    def metadata_extraction(self, query: str) -> dict:
        user_query = f"""
        {query}\n\n Dá-me apenas os metadados que tiraste desta query.\n\n
        Se não for indicado um ano em concreto, deves assumir o ano atual como 'legislation_date'.\n\n
        Hoje é dia {data_formatada}.
        """

        try:
            messages = self.query_metadata_few_shot_examples + [
                {"role": "user", "content": user_query}
            ]
            init_time = datetime.now()

            response = self.client.chat.completions.create(
                model="meta-llama/Llama-Vision-Free",
                messages=messages,
            )
            final_time = datetime.now()
            LOG.info(f"Metadata extraction took {final_time - init_time} seconds")

            metadata = response
        except json.JSONDecodeError:
            LOG.error("Failed to decode JSON response for metadata extraction.")
            metadata = {}
        finally:
            return {"metadata": metadata}


if __name__ == "__main__":
    preprocessor = Preprocessing()
    query = "Como funciona o processo de herança segundo a lei portuguesa?"
    expanded_queries = preprocessor._expand_query(
        query, preprocessor.query_expansion_few_shot_examples
    )
    print(expanded_queries)
    metadata = preprocessor.metadata_extraction(query)
    print(metadata)
