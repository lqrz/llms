"""Vector store."""

from typing import List
from llama_index.core.schema import TextNode, NodeWithScore
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.vector_stores.types import VectorStoreQueryMode, MetadataFilters
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse

from llms.commons.logger import logger

# TODO:
# figure out how vector store receives nodes, then queries, etc.


class VectorStore:
    """VectorStore."""

    def __init__(
        self,
        url: str,
        collection_name: str,
        nodes: List[TextNode],
        document_id_key: str,
        embeddings_model: HuggingFaceEmbedding,
        is_recreate_collection: bool,
        is_hybrid: bool = True,
    ):
        """Init."""
        self.url: str = url
        self.collection_name: str = collection_name
        self.embeddings_model: HuggingFaceEmbedding = embeddings_model
        self.client: QdrantClient = self._instantiate_client(url=url)
        self.vector_store: QdrantVectorStore = self._instantiate_vector_store(
            collection_name=self.collection_name,
            is_hybrid=is_hybrid,
            is_recreate=is_recreate_collection,
        )
        self.index: VectorStoreIndex = self._build_index(
            nodes=nodes, key=document_id_key
        )

    @staticmethod
    def _instantiate_client(url: str) -> QdrantClient:
        """Instantiate vector db client."""
        client = QdrantClient(url=url)
        return client

    def _instantiate_vector_store(
        self,
        collection_name: str,
        is_hybrid: bool,
        is_recreate: bool,
    ) -> QdrantVectorStore:
        """Instantiate vector store."""
        if is_recreate:
            _ = self._delete_collection()
        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=collection_name,
            enable_hybrid=is_hybrid,  # enable hybrid search
        )
        return vector_store

    def _collection_exists(self) -> bool:
        """Check if collection exists in the vector db."""
        try:
            _ = self.client.get_collection(self.collection_name)
            return True
        except UnexpectedResponse:
            return False

    def _delete_collection(self) -> None:
        """Delete existing collection."""
        if self._collection_exists():
            _ = logger.info(f"Deleting collection {self.collection_name}")
            _ = self.client.delete_collection(collection_name=self.collection_name)

    def is_node_in_index(self, key: str, value: str) -> bool:
        """Check if node is already in the vector db."""
        scroll_filter = Filter(
            must=[FieldCondition(key=key, match=MatchValue(value=value))]
        )

        _, point_id = self.client.scroll(
            collection_name=collection_name,
            scroll_filter=scroll_filter,
            limit=1,
            with_payload=False,
            with_vectors=False,
        )

        return point_id is not None

    def _filter_existing_nodes(self, nodes: List[TextNode], key: str) -> List[TextNode]:
        """Filter existing nodes."""
        nodes_to_keep: List[TextNode] = nodes[:]
        if self._collection_exists():
            for x in nodes[:]:
                value: str = x.metadata[key]
                if self.is_node_in_db(key=key, value=value):
                    _ = logger.warning(
                        f"Node with {key}={value} already in vector db. Skipping..."
                    )
                    nodes.remove(x)
                else:
                    _ = logger.info(f"Processing Node with {key}={value}")
        else:
            _ = logger.info(f"Processing all {len(nodes_to_keep)} nodes")

        return nodes_to_keep

    def _build_index(self, nodes: List[TextNode], key: str) -> VectorStoreIndex:
        """Build index."""
        nodes_to_insert: List[TextNode] = self._filter_existing_nodes(
            nodes=nodes, key=key
        )
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        index = VectorStoreIndex(nodes_to_insert, storage_context=storage_context)
        return index

    def run_semantic_search(self, query: str, top_k: int) -> List[NodeWithScore]:
        """Run semantic search."""
        retriever = self.index.as_retriever(
            embed_model=self.embeddings_model,
            vector_store_query_mode=VectorStoreQueryMode.DEFAULT,  # semantic
            similarity_top_k=top_k,
        )
        results: List[NodeWithScore] = retriever.retrieve(query)
        return results

    def run_keyword_search(self, query: str, top_k: int) -> List[NodeWithScore]:
        """Run keyword search."""
        retriever = self.index.as_retriever(
            embed_model=self.embeddings_model,
            vector_store_query_mode=VectorStoreQueryMode.SPARSE,  # keyword
            similarity_top_k=top_k,
        )
        results: List[NodeWithScore] = retriever.retrieve(query)
        return results

    def run_hybrid_search(
        self,
        query: str,
        top_k_each: int,
        top_k_final: int,
        alpha: float,
        metadata_filters: List[MetadataFilters],
    ) -> List[NodeWithScore]:
        """Run hybrid search."""
        retriever = self.index.as_retriever(
            embed_model=self.embeddings_model,
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
