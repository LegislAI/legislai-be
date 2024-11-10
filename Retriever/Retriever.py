#!/usr/bin/env/python3
import json
import logging
import os
import re
import subprocess
import time
from datetime import datetime
from multiprocessing import Process
from multiprocessing import Queue
from typing import Optional

from database.bin.utils import BM250RerankingModel
from database.DatabaseController import DatabaseController as dbc
from together import Together

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("retriever.log"), logging.StreamHandler()],
)
LOG = logging.getLogger("retriever")

subprocess.run("export TOKENIZERS_PARALLELISM=false", shell=True)

TOGETHER_API_KEY = os.getenv("ENHANCEMENT_API_KEY")


class Retriever:
    def __init__(self):
        self.databasecontroller = dbc()
        self.reranking_llm = Together(api_key=TOGETHER_API_KEY)
        self.bm25_model = BM250RerankingModel()

    def query(
        self,
        query: Optional[str],
        topk: Optional[int],
        metadata_filter: Optional[dict] = {},
    ):
        LOG.info(f"Received query: {query} with filters: {metadata_filter}")
        start = time.time()
        results = self.databasecontroller.query(
            query=query, top_k=topk, metadata_filter=metadata_filter
        )
        print(results)
        results = self.rerank_results(results, query, metadata_filter)
        end = time.time()
        LOG.info(f"Results for query:{query} in {end-start} seconds")
        return results

    # TODO: implement processing based on the metadata_filter
    def process_results(self, results, metadata_filter):
        # Return the original results, just join its text by ""
        return [
            {
                "id": result["id"],
                "metadata": result["metadata"],
                "score": result["score"],
                "text": "".join(result["metadata"]["text"]),
            }
            for result in results
        ]

    def bm250_rerank(self, query, results):
        documents = []
        for result in results:
            joint_result = "".join(result["text"])
            documents.append(joint_result)

        rerankinkg_result = self.bm25_model.bm25_rerank(query, documents)
        # sort the reraanked results by the bm25 score
        maped_id_result = []
        for result in rerankinkg_result:
            for result_id in results:
                if result["document"] == "".join(result_id["metadata"]["text"]):
                    maped_id_result.append(
                        {"id": result_id["id"], "score": result["bm25_score"]}
                    )
                    break
        return maped_id_result

    def interpolate_results(self, reranked_results, alpha):
        scores_dict = {}

        def add_scores(source_results, source_name):
            for item in source_results:
                doc_id = item["id"]
                score = item["score"]
                if doc_id not in scores_dict:
                    scores_dict[doc_id] = {
                        "database_score": 0,
                        "bm25_score": 0,
                        "llm_score": 0,
                    }
                scores_dict[doc_id][source_name] = score

        add_scores(reranked_results["database_results"], "database_score")
        add_scores(reranked_results["bm25_results"], "bm25_score")
        add_scores(reranked_results["llm_reranking"], "llm_score")

        interpolated_results = []

        for doc_id, scores in scores_dict.items():
            interpolated_score = (
                alpha * scores["database_score"]
                + alpha * scores["bm25_score"]
                + alpha * scores["llm_score"]
            )
            interpolated_results.append({"id": doc_id, "score": interpolated_score})

        interpolated_results = sorted(
            interpolated_results, key=lambda x: x["score"], reverse=True
        )
        return interpolated_results

    # llm based reranking
    # https://huggingface.co/cmarkea/bloomz-3b-reranking#dataset
    # td idf based reranking
    def rerank_results(self, results, query, metadata_filter):
        # tf idf from query with the results
        process_results = self.process_results(results, metadata_filter)
        bm25_results = self.bm250_rerank(query, process_results)
        llm_reranking = self.llm_rerank(query, process_results)

        # interpolate the rankings with 0.3 percent influence in every reranked result
        reranked_results = {
            "database_results": [
                {"id": result["id"], "score": result["score"]} for result in results
            ],
            "bm25_results": bm25_results,
            "llm_reranking": llm_reranking,
        }

        results = self.interpolate_results(reranked_results, 0.3)
        return results

    def llm_rerank(self, query, results):
        LOG.info(f"Reranking documents using an llm for query: {query}")
        documents_json = ", ".join(
            [
                f'{{"id": "{result["id"]}", "text": "{result["text"]}"}}'
                for result in results
            ]
        )
        prompt = f"""
           Tens acesso a uma função que baseada numa query atribui relevância a diversos documentos de suporte.
           Baseado no contexto da seguinte questão {query}, qual do texto presente dos documentos abaixo é mais relevante?
            Documentos:
                {documents_json}

            ###

           Para atribuir a relevância dos documentos à questão, usa a seguinte estrutura:

            <function=rerank>
            {{
                "query": "{query}",
                "results": {{
                    "documents": [ "id" : "document_id", "score" : "similarity_score" ]
                }}
            }}
            </function>

            Lembra-te:
            - Responde apenas no formato JSON mostrado.
            - Começa com <function=rerank> e termina com </function>.
            - Se não tiveres certeza, utiliza a ordenação original.
            - Atribui um valor "score" entre 0 e 100 para cada documento que represente a relevância do documento para a questão.
            - Na resposta devolve apenas os ids dos documentos por ordem de relevância.
            - Usa vírgulas para separar os elementos.
            - Todos os documentos que tenhas menos de 70% de certeza que são relevantes, deves descartar.
            - Usa chavetas para agrupar os elementos.
            """

        #   Lembra-te:
        # - Responde apenas no formato JSON mostrado.
        # - Começa com <function=rerank> e termina com </function>.
        # - Se não tiveres certeza, utiliza a ordenação original.
        # - Nas entradas multilinha, retira os caracteres \\n e coloca tudo na mesma linha de forma a respeitar os critérios da estrutura json.
        # - Usa aspas duplas para frases.
        # - Na resposta devolve apenas os ids dos documentos por ordem de relevância.
        # - Os documentos no resultado devem ser mantidos com a mesma estrutura dos originais.
        # - Mantém a estrutura dos resultados iguais aos originais
        # - Usa vírgulas para separar os elementos.
        # - Todos os documentos que tenhas menos de 80% de certeza que são relevantes, deves descartar.
        # - Usa chavetas para agrupar os elementos.
        try:

            prompt = {"role": "user", "content": prompt}

            init_time = datetime.now()

            response = self.reranking_llm.chat.completions.create(
                model="meta-llama/Llama-Vision-Free", messages=[prompt], temperature=0
            )
            final_time = datetime.now()
            LOG.info(f"LLM reranking took {final_time - init_time} seconds")
            metadata = response.choices[0].message.content
            result = self.parse_tool_response(metadata)

        except json.JSONDecodeError:
            LOG.error("Failed to decode JSON response for the llm reranking.")
            result = {}
        except Exception as e:
            LOG.error(
                f"Error reranking documents using an llm, for query: {query}, error: {e}"
            )
            result = {}
        finally:
            return result

    def parse_tool_response(self, response: str) -> dict:
        function_regex = r"<function=(\w+)>(.*?)</function>"
        match = re.search(function_regex, response, re.DOTALL)

        if match:
            _, args_string = match.groups()
            try:
                args = json.loads(args_string)
                documents = args.get("results", {}).get("documents", [])

                return documents

            except json.JSONDecodeError as error:
                LOG.error(f"Error parsing JSON arguments: {error}")
                LOG.debug(f"Failed JSON content: {args_string}")
                return {}
        else:
            LOG.warning("No function tag found in response.")
            return {}


if __name__ == "__main__":
    retriever = Retriever()
    results = retriever.query(query="Como posso extinguir uma associação?", topk=5)
    print(results)
