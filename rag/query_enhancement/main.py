import json
import logging
import os
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from queue import Queue
from threading import Thread
from typing import List

import spacy
from dotenv import load_dotenv
from together import Together

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

load_dotenv()

QUERY_ENHANCEMENT_PATH = Path("rag/query_enhancement").resolve()

ENHANCEMENT_API_KEY = os.getenv("ENHANCEMENT_API_KEY")
EXTRACTION_API_KEY = os.getenv("EXTRACTION_API_KEY")
CLASSIFIER_MODEL = QUERY_ENHANCEMENT_PATH / "classifier/models/model-best"

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
        self.classifier_model = spacy.load(CLASSIFIER_MODEL)

    def query_enhancement(self, query: str, queue: Queue) -> None:
        query_expansion_prompt = f"""
        És um sistema de informação que processa queries dos utilizadores.
        Expande uma query dada em 2 queries semelhantes no seu significado.

        Estrutura:
        Segue a estrutura mostrada nos exemplos abaixo para gerar queries expandidas.

        Query a expandir: {query}

        <function=query_expansion>
        {{
            "query_original": "{query}",
            "queries_expandidas": ["Fornece várias alternativas para a query '{query}' aqui"]
        }}
        </function>

        Lembra-te:
        - Responde apenas no formato JSON mostrado.
        - Começa com <function=query_expansion> e termina com </function>.
        - As queries expandidas devem ser semelhantes em significado à query original.
        - As queries expandidas devem conter a mesma data da query original.
        - Gera apenas mais duas queries expandidas.
        - As queries expandidas devem ser diferentes entre si.
        - As queries expandidas devem ser diferentes da query original.
        - As queries expandidas devem ser mais curtas que a query original.
        - Usa aspas duplas para strings.
        - Usa vírgulas para separar os elementos.
        - Usa chavetas para agrupar os elementos.
        """
        result = self._expand_query(
            query_expansion_prompt, self.query_expansion_few_shot_examples
        )
        queue.put({"queries_expanded": result})

    def _expand_query(self, query: str, few_shot_examples: list) -> dict:
        try:
            messages = few_shot_examples + [{"role": "user", "content": query}]
            init_time = datetime.now()

            response = self.enhancement_client.chat.completions.create(
                model="mistralai/Mistral-7B-Instruct-v0.1",
                messages=messages,
                temperature=0,
            )

            expanded_queries = response.choices[0].message.content
            expanded_queries = self.parse_tool_response(expanded_queries)

            final_time = datetime.now()
            LOG.info(f"Query expansion took {final_time - init_time} seconds")

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
            "resumo": "resumo da legislação aqui",
            "assunto": "principal tópico legal aqui"
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

            metadata = response.choices[0].message.content
            metadata = self.parse_tool_response(metadata)

            final_time = datetime.now()
            LOG.info(f"Metadata extraction took {final_time - init_time} seconds")

        except json.JSONDecodeError:
            LOG.error("Failed to decode JSON response for metadata extraction.")
            metadata = {}
        finally:
            queue.put({"metadata": metadata})

    def classify_query(self, query: str, queue: Queue) -> None:
        init_time = datetime.now()
        result = self.classifier_model(self._remove_stopwords(query))
        sorted_results = sorted(result.cats.items(), key=lambda x: x[1], reverse=True)[
            0
        ]
        final_time = datetime.now()
        LOG.info(f"Query classification took {final_time - init_time} seconds")
        queue.put({"theme": sorted_results})

    def _remove_stopwords(self, text: str) -> str:
        doc = self.classifier_model(text)
        filtered_words = [
            token.text for token in doc if not token.is_stop and not token.is_punct
        ]
        return " ".join(filtered_words)

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

    def parse_results(self, results: dict) -> dict:
        metadata = results.get("metadata", {})
        data_legislacao = metadata.get("data_legislacao", None)
        theme = results.get("theme", None)
        expanded_queries = results.get("queries_expanded", [])
        payload = {
            "metadata_filter": {
                "expanded_queries": expanded_queries.get("queries_expandidas", []),
                "data_legislacao": data_legislacao,
                "theme": theme[0] if theme[1] > 0.8 else None,
            },
            "additional_data": {
                "resumo": metadata.get("resumo", None),
                "assunto": metadata.get("assunto", None),
            },
        }
        return payload

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
        threads = []

        for method_name in method_names:
            method = method_mapping[method_name]
            t = Thread(target=method, args=(query, queue))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        results = {}
        while not queue.empty():
            results.update(queue.get())

        final_time = datetime.now()
        LOG.info(f"Processing query took {final_time - init_time} seconds")
        return self.parse_results(results)
