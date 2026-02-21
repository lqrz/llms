"""Ingestion."""

from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import TitleExtractor
from llama_index.core.vector_stores.types import (
    MetadataFilters,
    MetadataFilter,
    FilterOperator,
    FilterCondition,
)
from llama_index.core.schema import Document, TextNode, MetadataMode
from typing import List
import re

from llms.agent.rag.vector_store import VectorStore


def get_documents(path_input: str) -> List[Document]:
    """Get reader."""
    reader = SimpleDirectoryReader(input_dir=path_input)
    documents: List[Document] = reader.load_data(show_progress=True)
    return documents


def modify_document_text_template(document: Document, text_template: str):
    """Modify document text template."""
    document.text_template = text_template


def select_document_metadata(
    document: Document, keys_to_exclude: List[str], keys_to_include: List[str]
):
    """Select document metadata."""
    for key in keys_to_exclude:
        # excluded_embed_metadata_keys
        if key not in document.excluded_embed_metadata_keys:
            document.excluded_embed_metadata_keys.append(key)

        # excluded_llm_metadata_keys
        if key not in document.excluded_llm_metadata_keys:
            document.excluded_llm_metadata_keys.append(key)

    for key in keys_to_include:
        # excluded_embed_metadata_keys
        if key in document.excluded_embed_metadata_keys:
            document.excluded_embed_metadata_keys.remove(key)

        # excluded_llm_metadata_keys
        if key in document.excluded_llm_metadata_keys:
            document.excluded_llm_metadata_keys.remove(key)


def augment_document_metadata(document: Document):
    """Augment document metadata."""
    filename_re = re.compile(
        r"^\s*(?P<year>\d{4})\s+(?P<quarter>Q[1-4])\s+(?P<company>.+?)\s*$",
        re.IGNORECASE,
    )

    m = filename_re.match(document.metadata.get("file_name").strip(".pdf"))
    document.metadata["year"] = m.group("year")
    document.metadata["quarter"] = m.group("quarter")
    document.metadata["company"] = m.group("company")

    if "file_name" not in document.excluded_embed_metadata_keys:
        document.excluded_embed_metadata_keys.append("file_name")
    if "file_name" not in document.excluded_llm_metadata_keys:
        document.excluded_llm_metadata_keys.append("file_name")


def modify_document_metadata(
    documents: List[Document],
    text_template: str,
    keys_to_exclude: List[str],
    keys_to_include: List[str],
):
    """Modify. document metadata."""
    for d in documents:
        _ = modify_document_text_template(document=d, text_template=text_template)
        _ = select_document_metadata(
            document=d, keys_to_exclude=keys_to_exclude, keys_to_include=keys_to_include
        )
        _ = augment_document_metadata(document=d)


def ingest_data(
    path_input_data: str,
    vector_store_url: str,
    collection_name: str,
    is_hybrid: bool,
    is_recreate_collection: bool,
    document_id_key: str,
    embeddings_model_name: str,
    chunk_size: int,
    chunk_overlap: int,
    text_template: str,
    keys_to_exclude: List[str],
    keys_to_include: List[str],
):
    """Ingest data."""
    documents: List[Document] = get_documents(path_input=path_input_data)

    _ = modify_document_metadata(
        documents=documents,
        text_template=text_template,
        keys_to_include=keys_to_include,
        keys_to_exclude=keys_to_exclude,
    )

    # instantiate HuggingFace embedding model
    embeddings_model = HuggingFaceEmbedding(
        model_name=embeddings_model_name,
    )

    # instantiate transformation pipeline
    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
            # TitleExtractor(),
            embeddings_model,
        ]
    )

    # transform documents
    nodes: List[TextNode] = pipeline.run(documents=documents)

    _ = VectorStore(
        url=vector_store_url,
        collection_name=collection_name,
        nodes=nodes,
        document_id_key=document_id_key,
        embeddings_model=embeddings_model,
        is_hybrid=is_hybrid,
        is_recreate_collection=is_recreate_collection,
    )


if __name__ == "__main__":

    path_input_data: str = ""
    embeddings_model_name: str = "BAAI/bge-small-en-v1.5"
    chunk_size: int = 100
    chunk_overlap: int = 0
    text_template: str = (
        "<metadata>\n{metadata_str}\n</metadata>\n\n<content>\n{content}\n</content>"
    )
    keys_to_exclude: List[str] = ["page_label", "file_path"]
    keys_to_include: List[str] = []
