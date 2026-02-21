"""Vector store."""

from typing import List
from llama_index.core.schema import TextNode, NodeWithScore
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.vector_stores.types import VectorStoreQueryMode, MetadataFilters
from qdrant_client import QdrantClient

# TODO:
# singleton
# figure out how vector store receives nodes, then queries, etc.
# recreate collection?
# how to prevent inserting duplicate docs?


class VectorStore:
    """VectorStore."""

    def __init__(self, url: str, collection_name: str):
        pass

    def instantiate_vector_store(
        self, url: str, collection_name: str, is_hybrid: bool = True
    ):
        client = QdrantClient(url=url)
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=collection_name,
            enable_hybrid=is_hybrid,  # enable hybrid search
        )

    def build_index(self, nodes: List[TextNode]):
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(nodes, storage_context=storage_context)

    def run_semantic_search(
        self, embeddings_model, query: str, top_k: int
    ) -> List[NodeWithScore]:
        """Run semantic search."""
        retriever = self.index.as_retriever(
            embed_model=embeddings_model,
            vector_store_query_mode=VectorStoreQueryMode.DEFAULT,  # semantic
            similarity_top_k=top_k,
        )
        results: List[NodeWithScore] = retriever.retrieve(query)
        return results

    def run_keyword_search(
        self, embeddings_model, query: str, top_k: int
    ) -> List[NodeWithScore]:
        """Run keyword search."""
        retriever = self.index.as_retriever(
            embed_model=embeddings_model,
            vector_store_query_mode=VectorStoreQueryMode.SPARSE,  # keyword
            similarity_top_k=top_k,
        )
        results: List[NodeWithScore] = retriever.retrieve(query)
        return results

    def run_hybrid_search(
        self,
        embeddings_model,
        query: str,
        top_k_each: int,
        top_k_final: int,
        alpha: float,
        metadata_filters: List[MetadataFilters],
    ) -> List[NodeWithScore]:
        """Run hybrid search."""
        retriever = self.index.as_retriever(
            embed_model=embeddings_model,
            vector_store_query_mode=VectorStoreQueryMode.HYBRID,  # semantic
            similarity_top_k=top_k_final,  # controls the final number of returned nodes (after fusion).
            sparse_top_k=top_k_each,  # how many nodes will be retrieved from each dense and sparse query.
            alpha=alpha,  # by default applies relative_score_fusion
            filters=metadata_filters,  # metadata
        )
        results: List[NodeWithScore] = retriever.retrieve(query)
        return results


if __name__ == "__main__":

    import os

    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    collection_name = "data"
