# Run Qdrant DB

Run it via `docker-compose`:

```bash
docker compose -f container/docker-compose.yml up qdrant --build
```

# Access Qdrant UI dashboard

Visualise the content of the vector database by acessing the Qdrant dashboard at `http://localhost:6333/dashboard`.

---

# Qdrant / LlamaIndex objects

## 1. QdrantClient (Qdrant’s native SDK client)

What it is: The official Python client for talking to the Qdrant server over HTTP/gRPC.

Purpose:
* Create/delete/list collections
* Upsert points (vectors + payload)
* Search/retrieve points
* Scroll, count, manage indexes, snapshots, etc.

Think of it as: “raw database connection + API methods”.

You could build an app using only QdrantClient and never touch LlamaIndex.

## 1. QdrantVectorStore (LlamaIndex adapter around Qdrant)

What it is: A LlamaIndex VectorStore implementation that wraps QdrantClient and translates LlamaIndex operations into Qdrant operations.

You need a QdrantClient to instantiate a QdrantVectorStore:

```python
vector_store = QdrantVectorStore(
            client=client,
            collection_name=collection_name,
            enable_hybrid=is_hybrid,  # enable hybrid search
        )
```

## 1. StorageContext (LlamaIndex’s storage wiring)

What it it: LlamaIndex object that allows you to customize where ingested documents (i.e., Node objects), embedding vectors, and index metadata are stored.

Lets you mix-and-match storage backends (e.g., Qdrant for vectors + Redis for docstore + filesystem for index metadata).

It defines:
* vector store (QdrantVectorStore here)
* docstore (stores documents/nodes)
* index store (stores index metadata)

```python
storage_context = StorageContext.from_defaults(
    docstore=SimpleDocumentStore(),
    vector_store=SimpleVectorStore(),
    index_store=SimpleIndexStore(),
)
```

## 1. VectorStoreIndex (LlamaIndex’s index abstraction you query)

What it is: The LlamaIndex “Index” object you interact with at retrieval time.

Coordinates embedding + retrieval + (optionally) postprocessing/reranking hooks.

It’s a lightweight orchestrator that knows:
* which vector store to use (via StorageContext)
* which embedding model to use
* how to run queries and return `NodeWithScore` objects

---

# How to instantiate the VectorStoreIndex

It mainly depends on whether you want to **re-create the index or not** and which is the **starting point**.

## 1. Re-building the index each time from Documents `.from_documents()`

Starts from Documents, chunking, embeddings, upsert.

✅ Fastest for prototyping.
❌ Re-creates the vector store content.

```python
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    embed_model=embed_model,
    show_progress=True,
)
```

## 1. Re-building the index each time from Nodes `VectorStoreIndex(nodes)`

Starts from Nodes (Documents already chunked, optionally embedded as well).

✅ You already have an ingestion pipeline.
❌ Re-creates the vector store content.

```python
index = VectorStoreIndex(
    nodes,
    storage_context=storage_context,
    embed_model=embed_model,  # optional
)
```

## 1. Wrapper over an existing vector store

Source of truth: the QdrantVectorStore.

```python
index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
    storage_context=...,  # optional
    embed_model=...,  # optional
)
```

✅ Avoids re-creating the vector store content.
✅ Lightweight VectorStoreIndex wrapper around the vector store.
❌ If either the metadata or payload is not in the Qdrant vector store (e.g. it is handled by LlamaIndex) they won't be retrieved.

Note: Passing storage_context just tells it where to put/read docstore things if needed, but it doesn’t automatically retrieve the prior persisted index struct.

# 1. Load persisted storage context

Source of truth: the persisted StorageContext.

```python
storage_context = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(storage_context, index_id="my_index_id")
```

✅ Best for production.
✅ Avoids re-creating the vector store content.
❌ Not as lightweight as `.from_vector_store()` but much faster than rebuilding the index.

---

# Objects lifecycle best practices

* Keep the ingestion pipeline and the serving pipeline as independent processes.
* At startup, initialise a lightweight wrapper (VectorStoreIndex) around the vector store in the FastAPI lifespan.
* In the Langgraph nodes, instantiate a retriever per request (as it depends on: filters/top_k/fusion).

---

# How to ingest data

There are multiple ways to insert data, using an `IngestionPipeline` gives the most customisation freedom.

You need to take care of:
* Deduplication
* Double embedding

## Inserting via the VectorStore or VectorStoreIndex

Using an `IngestionPipeline`, data can be upserted either via the `QdrantVectorStore` or via LlamaIndex's `VectorStoreIndex`. Since the entrypoint is at two different abstraction layers, they both do different things beyond upserting.

Recall that you can setup the stores in such a way that the Qdrant vector store only handles vector storage while LlamaIndex is responsible for the payload and metadata storage; in such scenario, we will need to use the `VectorStoreIndex` to entry through LlamaIndex's abstraction.

✅ Best to use `IngestionPipeline` + LlamaIndex's `VectorStoreIndex` insertion since it allows you to manipulate nodes

### Via Qdrant's VectorStore

Setting the `vector_store` in the `IngestionPipeline:

```python
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
        TitleExtractor(),
    ],
    vector_store=vector_store,  # pass the vector store so the pipeline also upserts
)

pipeline.run(documents=documents)
```

Calling the `vector_store` separatedly:

```python
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
        TitleExtractor(),
    ],
)

nodes: List[TextNode] = pipeline.run(documents=documents)

vector_store.add(nodes=nodes)
```

### Via LlamaIndex's VectorStoreIndex

❌ Be careful with double embedding.

```python
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
        TitleExtractor(),
        # embeddings_model,  # optional: be careful here
    ],
)

nodes: List[TextNode] = pipeline.run(documents=documents)

vector_store_index.insert_nodes(nodes=nodes)
```

## How to avoid duplicates

The best strategy is to:
1. Run the `IngestionPipeline` without a `vector_store` to retrieve the list of nodes.
1. Use a node_id attribute to verify they do not already exist on the vector db.

Another way to do it (more automatically): By default, the vector db will upsert, so if you take care of deterministacally setting the `node.id_` attribute, it will use it to check if the node already exists (if so, updating it).

## How to avoid double embedding

There are two points in which we set the embeddings model:
1. when instantiating the `IngestionPipeline`.
1. when instantiating the `VectorStoreIndex`.

Thus, if we are using an `IngestionPipeline` and inserting via the `VectorStoreIndex`, the best way to make sure we are not double embedding is to only set the embeddings model in only one of them.