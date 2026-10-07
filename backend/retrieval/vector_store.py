import os
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_core.documents import Document
from backend.config import settings
from backend.embeddings.embedding_service import embedding_service

logger = logging.getLogger(__name__)

class ChromaVectorStoreManager:
    """ChromaDB persistent vector store manager for financial knowledge base."""

    def __init__(self, persist_dir: Optional[str] = None, collection_name: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME

        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Initialized ChromaDB at '{self.persist_dir}', collection '{self.collection_name}'")

    def _generate_doc_id(self, doc: Document) -> str:
        """Generate a deterministic unique document ID for duplicate detection."""
        if "chunk_id" in doc.metadata and doc.metadata["chunk_id"]:
            return doc.metadata["chunk_id"]
        meta_str = f"{doc.metadata.get('ticker')}_{doc.metadata.get('year')}_{doc.metadata.get('chunk_index', 0)}"
        content_hash = hashlib.md5(doc.page_content.encode("utf-8")).hexdigest()
        return f"{meta_str}_{content_hash}"

    def add_documents(self, documents: List[Document]) -> int:
        """
        Add documents to ChromaDB with automatic duplicate detection.
        Returns count of newly inserted or updated documents.
        """
        if not documents:
            return 0

        ids = [self._generate_doc_id(doc) for doc in documents]
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]

        # Generate embeddings
        embeddings = embedding_service.embed_documents(texts)

        # Upsert into ChromaDB (handles insert or update)
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        logger.info(f"Successfully upserted {len(documents)} document chunks into ChromaDB.")
        return len(documents)

    def _build_where_filter(
        self,
        ticker: Optional[str] = None,
        company: Optional[str] = None,
        year: Optional[int] = None,
        quarter: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Construct ChromaDB metadata filter object ($and clause when multiple filters are applied)."""
        conditions = []
        if ticker:
            conditions.append({"ticker": ticker.upper()})
        if company:
            conditions.append({"company": company})
        if year:
            conditions.append({"year": int(year)})
        if quarter:
            conditions.append({"quarter": quarter})
        if document_type:
            conditions.append({"document_type": document_type})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def similarity_search(
        self,
        query: str,
        top_k: int = 4,
        ticker: Optional[str] = None,
        year: Optional[int] = None,
        quarter: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> List[Document]:
        """Perform semantic similarity search with optional metadata filtering."""
        results = self.similarity_search_with_score(
            query=query,
            top_k=top_k,
            ticker=ticker,
            year=year,
            quarter=quarter,
            document_type=document_type
        )
        return [doc for doc, _ in results]

    def similarity_search_with_score(
        self,
        query: str,
        top_k: int = 4,
        ticker: Optional[str] = None,
        year: Optional[int] = None,
        quarter: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> List[Tuple[Document, float]]:
        """
        Perform vector similarity search returning (Document, similarity_score) tuples.
        ChromaDB cosine distance returned is converted to similarity score (1 - distance).
        """
        if not query or not query.strip():
            return []

        query_embedding = embedding_service.embed_query(query)
        where_clause = self._build_where_filter(ticker, None, year, quarter, document_type)

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k
        }
        if where_clause:
            kwargs["where"] = where_clause

        res = self.collection.query(**kwargs)

        documents_with_scores = []
        if res and res["documents"] and len(res["documents"]) > 0:
            doc_texts = res["documents"][0]
            metadatas = res["metadatas"][0]
            distances = res["distances"][0] if "distances" in res and res["distances"] else [0.0] * len(doc_texts)

            for text, meta, dist in zip(doc_texts, metadatas, distances):
                # Cosine distance to similarity conversion
                similarity = max(0.0, 1.0 - float(dist))
                doc = Document(page_content=text, metadata=meta or {})
                documents_with_scores.append((doc, similarity))

        return documents_with_scores

    def get_collection_count(self) -> int:
        """Return total document count in collection."""
        return self.collection.count()

    def get_collection_stats(self) -> Dict[str, Any]:
        """Return total document count and collection statistics."""
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "total_chunks": count,
            "persist_dir": self.persist_dir
        }

    def clear_collection(self):
        """Reset or clear all documents from collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

vector_store = ChromaVectorStoreManager()
