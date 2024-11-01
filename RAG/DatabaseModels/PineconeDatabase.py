import logging
import os
import time
from typing import List
from typing import Optional
from uuid import uuid4

from bin.Models import EmbeddingDocument
from bin.utils import DenseEmbeddingModel
from bin.utils import EmbeddingModel
from bin.utils import SparseEmbeddingModel
from dotenv import load_dotenv
from pinecone import Pinecone
from pinecone import ServerlessSpec

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("pinecone_db_log.log"), logging.StreamHandler()],
)
LOG = logging.getLogger("PINECONE")


class PineconeDatabase:
    def __init__(self):
        load_dotenv()
        self.embeddings = EmbeddingModel()
        self.sparse_embeddings = SparseEmbeddingModel()
        self.dense_embeddings = DenseEmbeddingModel()
        self.db = self.init_database(database_name="legislai")

    def init_database(self, database_name) -> Pinecone:
        LOG.info("Initializing Pinecone database")
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        database = Pinecone(api_key=pinecone_api_key)
        self.create_database(database_name=database_name, database=database)
        return database.Index(database_name)

    def insert_into_database(self, payload: EmbeddingDocument):
        try:
            dense_embedding = self.dense_embeddings.embed_query(
                payload.metadata["text"]
            )
            sparse_embedding = self.sparse_embeddings.embed_query(
                payload.metadata["text"]
            )
            sparse_embedding = {
                "indices": list(sparse_embedding.keys()),
                "values": list(float(x) for x in sparse_embedding.values()),
            }
            self.db.upsert(
                vectors=[
                    {
                        "id": payload.id,
                        "values": dense_embedding,
                        "sparse_values": sparse_embedding,
                        "metadata": payload.metadata,
                    }
                ]
            )
            LOG.info("Inserted payload into database")
        except Exception as e:
            LOG.error(f"Error inserting payload: {payload} into database: {e}")

    def test_insert(self):
        LOG.info("Testing insert")
        test_encoding = self.embeddings.embed_documents("test")[0]
        test_id = str(uuid4())
        self.db.upsert(vectors=[(test_id, test_encoding, {"text": "teste"})])
        init_time = time.time()
        _ = self.query("teste", top_k=1)
        LOG.info(f"Query time: {time.time() - init_time} seconds")

    def query(self, query: str, metadata_filter: dict = {}, top_k: int = 5):
        try:
            results = self.hybrid_query(query, top_k, alpha=0.3, filter=metadata_filter)
            return results
        except Exception as e:
            LOG.error(f"Error querying database: {e}, query: {query}")
            return

    def hybrid_scale(self, dense, sparse: dict, alpha: float):
        if alpha < 0 or alpha > 1:
            raise ValueError("Alpha must be between 0 and 1")

        hsparse = {
            "indices": list(sparse.keys()),
            "values": [float(v) * (1 - alpha) for v in sparse.values()],
        }
        hdense = [v * alpha for v in dense]
        return hdense, hsparse

    def hybrid_query(self, question, top_k, alpha, metadata_filter):
        sparse_vec = self.sparse_embeddings.embed_query(question)
        dense_vec = self.dense_embeddings.embed_query(question)
        dense_vec, sparse_vec = self.hybrid_scale(dense_vec, sparse_vec, alpha)
        result = self.db.query(
            vector=dense_vec,
            sparse_vector=sparse_vec,
            top_k=top_k,
            include_metadata=True,
            fitler=metadata_filter,
        )
        return result

    def rerank_results(self, results, query, top_k, alpha):
        reranked_results = []
        for result in results:
            dense_vec = result["values"]
            sparse_vec = result["sparse_values"]
            dense_vec, sparse_vec = self.hybrid_scale(dense_vec, sparse_vec, alpha)
            reranked_result = self.db.query(
                vector=dense_vec,
                sparse_vector=sparse_vec,
                top_k=top_k,
                include_metadata=True,
            )
            reranked_results.append(reranked_result)
        return reranked_results

    def create_database(
        self,
        database_name: str,
        database: Pinecone,
        database_spec: Optional[dict] = None,
    ):
        if database_name not in database.list_indexes().names():
            try:
                LOG.info(f"Database does not exist, creating database {database_name}")
                embedding_vector_dimension = (
                    self.get_embedding_model_size()
                    if database_spec is None
                    else database_spec["dimension"]
                )
                metric = (
                    "dotproduct" if database_spec is None else database_spec["metric"]
                )
                database.create_index(
                    name=database_name,
                    dimension=embedding_vector_dimension,
                    metric=metric,
                    spec=ServerlessSpec(cloud="aws", region="eu-west-1")
                    if database_spec is None
                    else database_spec["spec"],
                )
                LOG.info(
                    f"Created Database with name {database_name}\n"
                    f"Dimension: {embedding_vector_dimension}\n"
                    f"Metric: {metric}"
                )
            except Exception as e:
                LOG.error(f"Error creating database {database_name}: {e}")

    def get_embedding_model_size(self) -> int:
        return len(self.dense_embeddings.embed_query("teste"))


if __name__ == "__main__":
    pdb = PineconeDatabase()
