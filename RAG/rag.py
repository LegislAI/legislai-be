from functools import lru_cache
from queue import Queue
from threading import Thread

from prompt_specialists.pipeline import MultiHopRAG
from prompt_specialists.streaming import stream_answer
from QueryEnhancement.Preprocessing import Preprocessing
from Retriever.retriever import Retriever


class RAG:
    def __init__(self):
        self.retriever = Retriever()
        self.preprocessing = Preprocessing()
        self.hop_rag = MultiHopRAG()

    @lru_cache(maxsize=100)
    def query(self, query: str, topk: int) -> dict:
        query_preprocessing = self.preprocessing.process_query(
            query=query, method_names=("all",)
        )
        expanded_queries = query_preprocessing.get("expanded_queries", [])
        metadata_filter = query_preprocessing.get("metadata_filter", {})
        additional_data = query_preprocessing.get("additional_data", {})
        queue = Queue()
        threads = []
        expanded_queries.append(query)
        for expanded_query in expanded_queries:
            t = Thread(
                target=self.retriever.query,
                args=(expanded_query, topk, queue, metadata_filter),
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        results = {}
        while not queue.empty():
            queue_element = queue.get()
            results.update(queue_element)

        payload = {
            "code": metadata_filter.get("theme", None),
            "context_rag": [],
            "question": query,
        }

        for result in results.keys():
            documents = results.get(result)
            for document in documents:
                metadata = document.get("metadata", [])
                payload["context_rag"].append(
                    {
                        "article_title": metadata["title"],
                        "date": metadata_filter["data_legislacao"],
                        "url": metadata["link"],
                        "article_name": metadata["epigrafe"],
                        "content": metadata["text"],
                    }
                )

        # response = stream_answer(
        #     context_rag=payload.get("context_rag"), user_question=query, code_rag=None
        # )
        response = self.hop_rag(payload.get("context_rag"), user_question=query)


if __name__ == "__main__":
    RAG().query("O trabalhador estudante tem direito a férias?", 6)
