from functools import lru_cache
from queue import Queue
from threading import Thread

from QueryEnhancement.Preprocessing import Preprocessing
from Retriever.retriever import Retriever


class RAG:
    def __init__(self):
        self.retriever = Retriever()
        self.preprocessing = Preprocessing()

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
        print(results)
        # Retrieval
        # results = self.retriever.query(query=query, topk=topk, metadata_filter=metadata_filter)
        # print(results)
        # return results


if __name__ == "__main__":
    RAG().query("Como posso extinguir uma associação?", 5)
