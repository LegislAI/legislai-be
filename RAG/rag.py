# from Retriever.retriever import Retriever
from multiprocessing import freeze_support

from QueryEnhancement.Preprocessing import Preprocessing


class RAG:
    def __init__(self):
        # self.retriever = Retriever()
        self.preprocessing = Preprocessing()
        freeze_support()

    def query(self, query: str, topk: int) -> dict:
        # Query Enhancement
        query_preprocessing = self.preprocessing.process_query(
            query=query, method_names=("all",)
        )
        print(query_preprocessing)
        # Retrieval
        # results = self.retriever.query(query, topk)
        # return results


RAG().query("Como funciona o processo de herança segundo a lei portuguesa?", 5)
