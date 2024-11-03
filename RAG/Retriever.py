#!/usr/bin/env/python3
import logging
import time
from typing import Optional

from database.DatabaseController import DatabaseController as dbc
from rank_bm25 import BM25Okapi

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("retriever.log"), logging.StreamHandler()],
)
LOG = logging.getLogger("retriever")


class Retriever:
    def __init__(self):
        self.databasecontroller = dbc()

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

    def process_results(self, results, metadata_filter):
        # Date based processing
        return results

    def bm250_rerank(self, query, results):
        documents = [result["metadata"]["text"].split(" ") for result in results]
        bm25 = BM25Okapi(documents)
        scores = bm25.get_scores(query.split(" "))
        # TODO
        # Output as {"bm250" : score, "db_similarity_score" : score, "document" : result }
        results = sorted(list(zip(scores, results)), key=lambda x: x[0], reverse=True)
        return results

    # llm based reranking
    # https://huggingface.co/cmarkea/bloomz-3b-reranking#dataset
    # td idf based reranking
    #
    def rerank_results(self, results, query, metadata_filter):
        # tf idf from query with the results
        process_results = self.process_results(results, metadata_filter)
        bm25_results = self.bm250_rerank(query, process_results)
        llm_reranking = self.llm_rerank(query, process_results)
        pass

    def llm_rerank(self, query, results):
        prompt = f"""
           Baseado no contexto da seguinte questão, qual dos documentos abaixo é mais relevante?
           ###
           Questão: {query}
           ###
           Documentos:
            { "Documento {i}:\n " }
           ###
           Apresenta os resultados com a seguinte estrutura:
            Documento: x
            Relevância: 0.98

            Documento: y
            Relevância: 0.75

            Documento: z
            Relevância: 0.2

            """
        for result in results:
            prompt += f"""
            {result["metadata"]["text"]}
            """


if __name__ == "__main__":
    retriever = Retriever()
    results = retriever.query(query="test", topk=5)
    print(results)
