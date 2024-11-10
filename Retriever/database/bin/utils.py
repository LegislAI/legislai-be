import asyncio
from collections import Counter
from typing import Dict
from typing import List
from typing import Optional

import torch
from langchain_core.embeddings.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForMaskedLM
from transformers import AutoTokenizer


class EmbeddingModel(Embeddings):
    def __init__(
        self,
        model_name: Optional[str] = "dunzhang/stella_en_1.5B_v5",
        normalize_embeddings: Optional[bool] = False,
        show_progress: Optional[bool] = False,
        cache_dir: Optional[str] = ".cache",
    ):
        self.model_name = model_name
        self.normalize_embeddings = normalize_embeddings
        self.show_progress = show_progress
        self.embedding_model = HuggingFaceEmbeddings(
            cache_folder=cache_dir,
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": normalize_embeddings},
            show_progress=show_progress,
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embedding_model.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self.embedding_model.embed_query(text)

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        return await asyncio.get_event_loop().run_in_executor(
            None, self.embed_documents, texts
        )

    async def aembed_query(self, text: str) -> List[float]:
        return await asyncio.get_event_loop().run_in_executor(
            None, self.embed_query, text
        )


class DenseEmbeddingModel(Embeddings):
    def __init__(
        self,
        model_name: Optional[str] = "rufimelo/Legal-BERTimbau-sts-large-ma-v3",
        cache_dir: Optional[str] = ".cache",
    ):
        self.model_name = model_name
        self.embedding_model = SentenceTransformer(model_name, cache_folder=cache_dir)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embedding_model.encode(
            texts, convert_to_tensor=True, show_progress_bar=False
        ).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embedding_model.encode(
            text, convert_to_tensor=True, show_progress_bar=False
        ).tolist()

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        return await asyncio.get_event_loop().run_in_executor(
            None, self.embed_documents, texts
        )

    async def aembed_query(self, text: str) -> List[float]:
        return await asyncio.get_event_loop().run_in_executor(
            None, self.embed_query, text
        )


class RerankingModel(Embeddings):
    def __init__(
        self,
        model_name: Optional[str] = "hkunlp/instructor-xl",
        cache_dir: Optional[str] = ".cache",
    ):
        self.model_name = model_name
        self.embedding_model = SentenceTransformer(model_name, cache_folder=cache_dir)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embedding_model.encode(
            texts, convert_to_tensor=True, show_progress_bar=False
        ).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embedding_model.encode(
            text, convert_to_tensor=True, show_progress_bar=False
        ).tolist()

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        return await asyncio.get_event_loop().run_in_executor(
            None, self.embed_documents, texts
        )

    async def aembed_query(self, text: str) -> List[float]:
        return await asyncio.get_event_loop().run_in_executor(
            None, self.embed_query, text
        )


class SparseEmbeddingModel(Embeddings):
    def __init__(
        self,
        query_model: Optional[str] = "naver/efficient-splade-V-large-query",
        cache_dir: Optional[str] = ".cache",
    ):
        # self.tokenizer_docs = AutoTokenizer.from_pretrained(docs_model, cache_dir=cache_dir)
        # self.model_docs = AutoModelForMaskedLM.from_pretrained(docs_model, cache_dir=cache_dir)

        self.tokenizer_query = AutoTokenizer.from_pretrained(
            query_model, cache_dir=cache_dir
        )
        self.model_query = AutoModelForMaskedLM.from_pretrained(
            query_model, cache_dir=cache_dir
        )

    def embed_documents(self, texts: List[str]) -> List[Dict[int, float]]:
        return [
            self._sparse_encode(text, self.tokenizer_docs, self.model_docs)
            for text in texts
        ]

    def embed_query(self, text: str) -> Dict[int, float]:
        return self._sparse_encode(text, self.tokenizer_query, self.model_query)

    def _sparse_encode(self, text: str, tokenizer, model) -> Dict[int, float]:
        tokenized_text = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            output = model(**tokenized_text)
        token_ids = tokenized_text["input_ids"].squeeze().tolist()
        sparse_vec = dict(Counter(token_ids))
        return sparse_vec

    async def aembed_documents(self, texts: List[str]) -> List[Dict[int, float]]:
        return await asyncio.get_event_loop().run_in_executor(
            None, self.embed_documents, texts
        )

    async def aembed_query(self, text: str) -> Dict[int, float]:
        return await asyncio.get_event_loop().run_in_executor(
            None, self.embed_query, text
        )


from rank_bm25 import BM25Okapi
from nltk.corpus import stopwords
import nltk
from collections import Counter
from typing import List, Dict, Optional
import torch
from langchain_core.embeddings.embeddings import Embeddings
from transformers import AutoTokenizer

nltk.download("stopwords")
STOP_WORDS = set(stopwords.words("portuguese"))


class BM250RerankingModel(Embeddings):
    def __init__(self, language: Optional[str] = "portuguese"):
        self.language = language
        self.tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")

    def preprocess_text(self, text: str) -> List[str]:
        return [word.lower() for word in text.split() if word.lower() not in STOP_WORDS]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        tokenized_documents = [self.preprocess_text(text) for text in texts]
        # print(f"tokenized documents: {tokenized_documents}")
        return tokenized_documents

    def embed_query(self, text: str) -> List[float]:
        return self.preprocess_text(text)

    def bm25_rerank(self, query: str, documents: List[str]) -> List[Dict[str, float]]:
        tokenized_documents = self.embed_documents(documents)
        tokenized_query = self.embed_query(query)

        bm25 = BM25Okapi(tokenized_documents)
        scores = bm25.get_scores(tokenized_query)

        # Rerank documents based on BM25 scores
        reranked_results = [
            {"bm25_score": score, "document": doc}
            for score, doc in zip(scores, documents)
        ]

        # Sort results by BM25 score in descending order
        reranked_results = sorted(
            reranked_results, key=lambda x: x["bm25_score"], reverse=True
        )

        return reranked_results

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Asynchronously embed documents using BM25.
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self.embed_documents, texts
        )

    async def aembed_query(self, text: str) -> List[float]:
        """
        Asynchronously embed a query using BM25.
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self.embed_query, text
        )


# bm25_model = BM250RerankingModel()

# documents = [
#     "Como posso extinguir uma associação?",
#     "Quais são os requisitos legais para dissolver uma associação?",
#     "Existem passos formais para encerrar uma organização?",
# ]

# query = "Como posso extinguir uma associação?"

# reranked_results = bm25_model.bm25_rerank(query, documents)

# for result in reranked_results:
#     print(f"Document: {result['document']}, BM25 Score: {result['bm25_score']}")
