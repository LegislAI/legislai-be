# from Retriever.retriever import Retriever
from multiprocessing import freeze_support

from QueryEnhancement.Preprocessing import Preprocessing


class RAG:
    def __init__(self):
        # self.retriever = Retriever()
        self.preprocessing = Preprocessing()
        self.query(
            "Como funciona o processo de herança segundo a lei portuguesa em 2022?", 5
        )

    def query(self, query: str, topk: int) -> dict:
        # Query Enhancement
        query_preprocessing = self.preprocessing.process_query(
            query=query, method_names=("all",)
        )
        print(query_preprocessing)
        # Retrieval
        results = self.retriever.query(query, topk)
        # return results


if __name__ == "__main__":
    freeze_support()
    RAG()
    # RAG().query("Como funciona o processo de herança segundo a lei portuguesa?", 5)
