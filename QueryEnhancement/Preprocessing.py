import json
import logging
import os
import re
from datetime import datetime
from functools import lru_cache
from multiprocessing import freeze_support
from multiprocessing import Process
from multiprocessing import Queue
from pathlib import Path
from typing import List

import spacy
from dotenv import load_dotenv
from together import Together

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

load_dotenv()

QUERY_ENHANCEMENT_PATH = Path("QueryEnhancement").resolve()

ENHANCEMENT_API_KEY = os.getenv("ENHANCEMENT_API_KEY")
EXTRACTION_API_KEY = os.getenv("EXTRACTION_API_KEY")
CLASSIFIER_MODEL = QUERY_ENHANCEMENT_PATH / "models/model-best"

data_atual = datetime.now()
data_formatada = data_atual.strftime("%Y-%m-%d")


class Preprocessing:
    def __init__(self):
        with open(
            QUERY_ENHANCEMENT_PATH / "bin/query_expansion_few_show_examples.json"
        ) as f:
            self.query_expansion_few_shot_examples = json.load(f)

        with open(
            QUERY_ENHANCEMENT_PATH / "bin/query_metadata_few_shot_examples.json"
        ) as f:
            self.query_metadata_few_shot_examples = json.load(f)

        self.enhancement_client = Together(api_key=ENHANCEMENT_API_KEY)
        self.extraction_client = Together(api_key=EXTRACTION_API_KEY)
        self.classifier_model = spacy.load(
            "QueryEnhancement/classifier/models/model-best"
        )

    def query_enhancement(self, query: str, queue: Queue) -> None:
        query_expansion_prompt = f"""
        És um sistema de informação que processa queries dos utilizadores.
        Expande uma query dada em 2 queries semelhantes no seu significado.

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

        <function=query_expansion>
        {{
            "query_original": "{query}",
            "queries_expandidas": ["Fornece várias alternativas para a query '{query}' aqui"]
        }}
        </function>

        Lembra-te:
        - Responde apenas no formato JSON mostrado.
        - Começa com <function=query_expansion> e termina com </function>.
        - Usa aspas duplas para strings.
        - Usa vírgulas para separar os elementos.
        - Usa chavetas para agrupar os elementos.
        """
        result = self._expand_query(
            query_expansion_prompt, self.query_expansion_few_shot_examples
        )
        queue.put(result)

    def _expand_query(self, query: str, few_shot_examples: list) -> dict:
        try:
            messages = few_shot_examples + [{"role": "user", "content": query}]
            init_time = datetime.now()

            response = self.enhancement_client.chat.completions.create(
                model="mistralai/Mistral-7B-Instruct-v0.1",
                messages=messages,
                temperature=0,
            )
            final_time = datetime.now()
            LOG.info(f"Query expansion took {final_time - init_time} seconds")

            expanded_queries = response.choices[0].message.content
            expanded_queries = self.parse_tool_response(expanded_queries)

        except json.JSONDecodeError:
            LOG.error("Failed to decode JSON response for query expansion.")
            expanded_queries = query
        finally:
            return expanded_queries

    def metadata_extraction(self, query: str, queue: Queue) -> None:
        user_query = f"""
        Tens acesso a uma função que extrai metadados de uma query.
        Para extrair metadados da query '{query}', usa o seguinte formato:

        <function=metadata_extraction>
        {{
            "data_legislacao": "data_legislacao",
            "data_pergunta": "{data_formatada}",
            "resumo": "Fornece um breve resumo do contexto legal de '{query}'",
            "assunto": "Fornece o tópico legal principal aqui"
        }}
        </function>


        Lembra-te:
        - Responde apenas no formato JSON mostrado.
        - Começa com <function=metadata_extraction> e termina com </function>.
        - Se não for indicado um ano em concreto, deves assumir o ano atual como 'data_legislacao'.
        - Hoje é dia {data_formatada}.
        - Usa aspas duplas para strings.
        - Usa vírgulas para separar os elementos.
        - Usa chavetas para agrupar os elementos.
        """

        try:
            messages = self.query_metadata_few_shot_examples + [
                {"role": "user", "content": user_query}
            ]
            init_time = datetime.now()

            response = self.extraction_client.chat.completions.create(
                model="meta-llama/Llama-Vision-Free", messages=messages, temperature=0
            )
            final_time = datetime.now()
            LOG.info(f"Metadata extraction took {final_time - init_time} seconds")

            metadata = response.choices[0].message.content
            metadata = self.parse_tool_response(metadata)

        except json.JSONDecodeError:
            LOG.error("Failed to decode JSON response for metadata extraction.")
            metadata = {}
        finally:
            queue.put({"metadata": metadata})

    def parse_tool_response(self, response: str) -> dict:
        function_regex = r"<function=(\w+)>(.*?)</function>"
        match = re.search(function_regex, response, re.DOTALL)

        if match:
            _, args_string = match.groups()
            try:
                args = json.loads(args_string.strip())
                return args

            except json.JSONDecodeError as error:
                LOG.error(f"Error parsing JSON arguments: {error}")
                LOG.debug(f"Failed JSON content: {args_string}")
                return {}
        else:
            LOG.warning("No function tag found in response.")
            return {}

    def _remove_stopwords(self, text: str) -> str:
        doc = self.classifier_model(text)
        filtered_words = [
            token.text for token in doc if not token.is_stop and not token.is_punct
        ]
        return " ".join(filtered_words)

    def classify_query(self, query: str, queue: Queue) -> None:
        result = self.classifier_model(self._remove_stopwords(query))
        sorted_results = sorted(result.cats.items(), key=lambda x: x[1], reverse=True)[
            0
        ]
        queue.put({"theme": sorted_results})

    @lru_cache(maxsize=100)
    def process_query(self, query: str, method_names: tuple[str] = ("all",)) -> dict:
        LOG.info(f"Processing query: {query}")
        init_time = datetime.now()

        method_mapping = {
            "query_enhancement": self.query_enhancement,
            "metadata_extraction": self.metadata_extraction,
            "classify_query": self.classify_query,
        }

        if method_names == ("all",):
            method_names = tuple(method_mapping.keys())

        LOG.info(f"Methods to be executed: {method_names}")
        queue = Queue()
        processes = []

        for method_name in method_names:
            method = method_mapping[method_name]
            p = Process(target=method, args=(query, queue))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

        results = {}
        while not queue.empty():
            results.update(queue.get())

        final_time = datetime.now()
        LOG.info(f"Processing query took {final_time - init_time} seconds")

        metadata = results.get("metadata", {})
        query_enchancement = results.get("queries_expanded", {})
        query_classification = results.get("theme", {})

        # parsed_results = {
        #     "metadata_filter" : {
        #         "data_legislacao" : results.get("data_legislacao", ""),
        #         "data_pergunta" : results.get("data_pergunta", ""),
        #         "document_name" : query_classification if query_classification.get("score")>,
        #     },
        #     "expanded_queries" : query_enchancement,
        #     "suporting_metadata" : {
        #         "resumo" : results.get("resumo", ""),
        #         "assunto" : results.get("metadata", {}).get("assunto", ""),
        #     }
        # }

        return results


if __name__ == "__main__":
    freeze_support()
    preprocessor = Preprocessing()
    query = "Como posso extinguir uma associação?"

    payload = preprocessor.process_query(query, method_names=("all",))
    print(payload)
