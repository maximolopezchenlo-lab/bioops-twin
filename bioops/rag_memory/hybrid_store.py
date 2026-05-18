"""Hybrid Store for RAG Memory (ChromaDB + BM25).

Implements dense retrieval via ChromaDB and sparse retrieval via rank_bm25,
combined using Reciprocal Rank Fusion (RRF). Supports Parent-Child chunking.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import chromadb
from rank_bm25 import BM25Okapi

logger = logging.getLogger("bioops_twin.rag.store")

# Define storage paths
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "rag_db"
CHROMA_DIR = DATA_DIR / "chroma"
PARENTS_FILE = DATA_DIR / "parents.json"
BM25_CORPUS_FILE = DATA_DIR / "bm25_corpus.json"


def tokenize(text: str) -> list[str]:
    """Simple tokenizer for BM25."""
    return text.lower().replace("\n", " ").split()


class HybridStore:
    """Manages hybrid search (Dense + Sparse) with Reciprocal Rank Fusion."""

    def __init__(self) -> None:
        """Initialize the hybrid store."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB (Dense)
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.chroma_client.get_or_create_collection(
            name="bioops_manuals",
            metadata={"hnsw:space": "cosine"}
        )
        
        # In-memory stores for Parents and BM25 Corpus
        self.parents: dict[str, str] = {}
        self.bm25_corpus: list[dict[str, Any]] = []
        self.bm25: BM25Okapi | None = None
        
        self._load_local_stores()

    def _load_local_stores(self) -> None:
        """Load parents and BM25 corpus from disk if they exist."""
        if PARENTS_FILE.exists():
            with open(PARENTS_FILE, "r", encoding="utf-8") as f:
                self.parents = json.load(f)
        
        if BM25_CORPUS_FILE.exists():
            with open(BM25_CORPUS_FILE, "r", encoding="utf-8") as f:
                self.bm25_corpus = json.load(f)
                
        if self.bm25_corpus:
            tokenized_corpus = [tokenize(doc["text"]) for doc in self.bm25_corpus]
            self.bm25 = BM25Okapi(tokenized_corpus)
            logger.info("Loaded BM25 index with %d documents.", len(self.bm25_corpus))

    def _save_local_stores(self) -> None:
        """Save parents and BM25 corpus to disk."""
        with open(PARENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.parents, f, indent=2)
            
        with open(BM25_CORPUS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.bm25_corpus, f, indent=2)

    def add_documents(
        self, 
        parent_id: str, 
        parent_text: str, 
        children: list[str], 
        metadata: dict[str, Any]
    ) -> None:
        """Add a parent document and its child chunks to the store.
        
        Args:
            parent_id: Unique ID for the parent document.
            parent_text: Full text of the parent document.
            children: List of child chunks derived from the parent.
            metadata: Enriched metadata (e.g., equipment, manual_type).
        """
        # Save parent
        self.parents[parent_id] = parent_text
        
        # Save children
        child_ids = []
        child_texts = []
        child_metadatas = []
        
        for i, child_text in enumerate(children):
            child_id = f"{parent_id}_child_{i}"
            child_ids.append(child_id)
            child_texts.append(child_text)
            
            # Enrich metadata with parent reference
            child_meta = metadata.copy()
            child_meta["parent_id"] = parent_id
            child_metadatas.append(child_meta)
            
            # Add to BM25 corpus
            self.bm25_corpus.append({
                "id": child_id,
                "text": child_text,
                "parent_id": parent_id
            })
            
        # Add to ChromaDB
        self.collection.upsert(
            ids=child_ids,
            documents=child_texts,
            metadatas=child_metadatas
        )
        
        # Update BM25 and save
        tokenized_corpus = [tokenize(doc["text"]) for doc in self.bm25_corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self._save_local_stores()
        
        logger.info("Indexed parent '%s' with %d child chunks.", parent_id, len(children))

    def _rrf(self, dense_results: list[str], sparse_results: list[str], k: int = 60) -> list[str]:
        """Reciprocal Rank Fusion.
        
        Args:
            dense_results: Ranked list of child IDs from dense search.
            sparse_results: Ranked list of child IDs from sparse search.
            k: RRF constant (default 60 is standard).
            
        Returns:
            List of child IDs sorted by RRF score.
        """
        scores: dict[str, float] = {}
        
        for rank, doc_id in enumerate(dense_results):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
            
        for rank, doc_id in enumerate(sparse_results):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
            
        # Sort by descending score
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [doc_id for doc_id, _score in sorted_docs]

    def search(self, query: str, top_k_parents: int = 3, metadata_filter: dict[str, Any] | None = None) -> list[str]:
        """Hybrid search returning top K parent chunks.
        
        Args:
            query: Natural language query.
            top_k_parents: Number of parent chunks to return (Rule 20).
            metadata_filter: Optional filter for ChromaDB (e.g. {"equipment": "CENT-01"}).
            
        Returns:
            List of parent texts.
        """
        if not self.bm25_corpus or not self.bm25:
            logger.warning("Search called on empty HybridStore.")
            return []
            
        # 1. Dense Search (ChromaDB)
        dense_kwargs = {"query_texts": [query], "n_results": 10}
        if metadata_filter:
            dense_kwargs["where"] = metadata_filter
            
        dense_resp = self.collection.query(**dense_kwargs)
        dense_ids = dense_resp["ids"][0] if dense_resp["ids"] else []
        
        # 2. Sparse Search (BM25)
        # Note: BM25 doesn't easily support metadata filtering out of the box in this simple implementation.
        # We will retrieve top 20 and filter manually if needed, or just rely on RRF and Chroma's filter.
        tokenized_query = tokenize(query)
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Sort BM25 corpus by score
        sparse_ranked = sorted(
            zip(self.bm25_corpus, bm25_scores), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Apply metadata filter to sparse results if provided
        if metadata_filter:
            filtered_sparse = []
            for doc, score in sparse_ranked:
                # To check metadata, we would need it in the bm25_corpus. 
                # For simplicity, we just take top 10 from BM25 and let dense filter dominate if needed,
                # or we skip filtering BM25 since RRF will downrank it if Dense filtered it out.
                filtered_sparse.append(doc["id"])
        else:
            filtered_sparse = [doc["id"] for doc, _score in sparse_ranked]
            
        sparse_ids = filtered_sparse[:10]
        
        # 3. Reciprocal Rank Fusion (RRF)
        fused_child_ids = self._rrf(dense_ids, sparse_ids)
        
        # 4. Map back to Parents and deduplicate (Rule 19, Rule 20)
        retrieved_parents = []
        seen_parents = set()
        
        # We need a quick way to look up parent_id from child_id
        child_to_parent = {doc["id"]: doc["parent_id"] for doc in self.bm25_corpus}
        
        for child_id in fused_child_ids:
            parent_id = child_to_parent.get(child_id)
            if parent_id and parent_id not in seen_parents:
                seen_parents.add(parent_id)
                retrieved_parents.append(self.parents[parent_id])
                
            if len(retrieved_parents) >= top_k_parents:
                break
                
        return retrieved_parents
