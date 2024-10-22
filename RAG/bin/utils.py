import asyncio
from typing import List
from typing import Optional

from langchain_core.embeddings.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings


class EmbeddingModel(Embeddings):
    # https://huggingface.co/spaces/mteb/leaderboard
    # "dunzhang/stella_en_1.5B_v5"
    def __init__(
        self,
        model_name: Optional[str] = "BAAI/bge-large-en-v1.5",
        normalize_embeddings: Optional[bool] = False,
        show_progress: Optional[bool] = False,
    ):
        self.model_name = model_name
        self.normalize_embeddings = normalize_embeddings
        self.show_progress = show_progress
        self.embedding_model = HuggingFaceEmbeddings(
            cache_folder=".cache",
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": normalize_embeddings},
            show_progress=show_progress,
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embedding_model.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self.embedding_model.embed_query(text)

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_documents, texts)

    async def aembed_query(self, text: str) -> List[float]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_query, text)
