#!/usr/bin/env/python3
import json
import logging
import os
import re
import subprocess
import time
from datetime import datetime
from queue import Queue
from threading import Thread
from typing import Optional

from rag.retriever.database.bin.utils import BM250RerankingModel
from rag.retriever.database.DatabaseController import DatabaseController as dbc
from together import Together

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("retriever.log"), logging.StreamHandler()],
)
LOG = logging.getLogger("retriever")

subprocess.run("export TOKENIZERS_PARALLELISM=false", shell=True)

TOGETHER_API_KEY = os.getenv("TOGETHER_AI_API_KEY")


class Retriever:
    def __init__(self):
        self.databasecontroller = dbc()
        self.reranking_llm = Together(api_key=TOGETHER_API_KEY)
        self.bm25_model = BM250RerankingModel()

    def query(
        self,
        query: Optional[str],
        topk: Optional[int],
        queue: Optional[Queue],
        metadata_filter: Optional[dict] = {},
    ):
        try:
            LOG.info(f"Received query: {query} with filters: {metadata_filter}")
            start = time.time()
            results = self.databasecontroller.query(query=query, top_k=topk)
            LOG.info(f"Results for query:{query} in {time.time()-start} seconds")
            results = self.rerank_results(results, query, metadata_filter)
            end = time.time()
            LOG.info(f"Results for query:{query} in {end-start} seconds")
        except:
            LOG.error(f"Error querying database for query: {query}")
            results = []
        finally:
            if queue:
                queue.put({query: results})
            else:
                return results

    def process_results(self, results, metadata_filter):
        return {
            result["id"]: {
                "id": result["id"],
                "metadata": result["metadata"],
                "score": result["score"],
                "text": "".join(result["metadata"]["text"]),
                "theme": result["metadata"].get("theme", ""),
                "source_url": result["metadata"].get("link", ""),
                "law_name": result["metadata"].get("law_name", ""),
                "title": result["metadata"].get("title", ""),
                "epigrafe": result["metadata"].get("epigrafe", ""),
            }
            for result in results
        }

    def bm250_rerank(self, query, results):
        documents = [result["text"] for result in results]

        rerankinkg_result = self.bm25_model.bm25_rerank(query, documents)
        maped_id_result = []
        for result in rerankinkg_result:
            for result_id in results:
                if result["document"] == result_id["text"]:
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
        bm25_results = self.bm250_rerank(query, process_results.values())
        llm_reranking = self.llm_rerank(query, process_results.values())

        reranked_results = {
            "database_results": [
                {"id": result["id"], "score": result["score"]} for result in results
            ],
            "bm25_results": bm25_results,
            "llm_reranking": llm_reranking,
        }
        interpolated_ranked_results = self.interpolate_results(reranked_results, 0.3)

        reranked_results = []
        for result in interpolated_ranked_results:
            result_id = result["id"]
            if result_id not in process_results:
                LOG.info(f"Document {result_id} not found in the interpolated results.")
                continue

            process_result = process_results[result_id]
            process_result["score"] = result["score"]
            reranked_results.append(process_result)
        return reranked_results

    def _rerank(self, prompt, queue: Queue):
        try:
            prompt = {"role": "user", "content": prompt}

            response = self.reranking_llm.chat.completions.create(
                model="google/gemma-2-9b-it", messages=[prompt], temperature=0
            )
            metadata = response.choices[0].message.content

            result = self.parse_tool_response(metadata)

        except json.JSONDecodeError as e:
            LOG.error("Failed to decode JSON response for LLM reranking.")
            LOG.debug(f"Error details: {e}")
            result = {}
        except Exception as e:
            LOG.error(f"Unexpected error during LLM reranking: {e}")
            result = {}
        finally:
            queue.put(result)

    def llm_rerank(self, query, results):
        LOG.info(f"Reranking documents using an LLM for query: {query}")
        answer_queue = Queue()
        threads = []
        init_time = datetime.now()

        # Create threads for reranking
        for document in results:
            document_json = json.dumps({"id": document["id"], "text": document["text"]})
            prompt = f"""
            Tens acesso a uma função que baseada numa query atribui relevância entre um documento e a questão do utilizador.
            Baseado no contexto da seguinte questão {query}, qual a relevância do texto seguinte?
                Documento:
                    {document_json}

                ###

            Para atribuir a relevância dos documentos à questão, usa a seguinte estrutura:

                <function=rerank>
                {{
                    "query": "{query}",
                    "results": {{
                        "documents": [{{ "id": "document_id", "score": similarity_score }}]
                    }}
                }}
                </function>

                Lembra-te:
                - Responde apenas no formato JSON mostrado.
                - Começa com <function=rerank> e termina com </function>.
                - Se não tiveres certeza, atribui o score de 80.
                - Atribui um valor "score" entre 0 e 100 para cada documento que represente a relevância do documento para a questão.
                - Na resposta devolve apenas os ids dos documentos por ordem de relevância.
                - Usa vírgulas para separar os elementos.
                - Todos os documentos que tenhas menos de 70% de certeza que são relevantes, deves descartar.
                - Usa chavetas para agrupar os elementos.
                """

            t = Thread(target=self._rerank, args=(prompt, answer_queue))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        aggregated_results = []
        while not answer_queue.empty():
            element = answer_queue.get()
            if isinstance(element, list):
                aggregated_results.extend(element)

        final_time = datetime.now()
        LOG.info(f"LLM reranking completed in {final_time - init_time}.")
        LOG.debug(f"Final aggregated results: {aggregated_results}")
        return aggregated_results

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
