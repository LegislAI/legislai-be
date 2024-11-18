from typing import List
from typing import Optional


class EmbeddingDocument:
    def __init__(
        self,
        doc_id: str,
        metadata: dict,
        embedding: Optional[List[float]] = None,
        sparse_embedding: Optional[List[float]] = None,
    ):
        self.id = doc_id
        self.embedding = embedding
        self.metadata = metadata
        self.sparse_embedding = sparse_embedding


class Payload:
    def __init__(self, user_id: Optional[str], query: str):
        self.user_id = user_id
        self.query = query
        self.timestamp = None
