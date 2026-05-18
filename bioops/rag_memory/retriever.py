"""ChromaDB RAG retriever for Milestone 3.

Implements hybrid search (BM25 + dense vectors)
with parent-child chunking.
"""

from __future__ import annotations

import logging
from bioops.rag_memory.hybrid_store import HybridStore

logger = logging.getLogger("bioops_twin.rag")

# Singleton store to avoid reloading BM25 and Chroma clients on every query
_store_instance: HybridStore | None = None

def get_store() -> HybridStore:
    """Get or initialize the HybridStore singleton."""
    global _store_instance
    if _store_instance is None:
        _store_instance = HybridStore()
    return _store_instance

def retrieve_context(query: str, equipment_id: str | None = None, top_k: int = 3) -> list[str]:
    """Retrieve relevant document chunks for a query using Hybrid Search.

    Args:
        query: The natural language query.
        equipment_id: Optional equipment ID to filter metadata (e.g. 'CENT-01').
        top_k: Number of parent chunks to retrieve (Rule 20).

    Returns:
        A list of relevant parent text chunks.
    """
    logger.info("retrieve_context: Hybrid Search for '%s'", query)
    store = get_store()
    
    metadata_filter = None
    if equipment_id:
        metadata_filter = {"equipment": equipment_id.upper()}
        
    results = store.search(query=query, top_k_parents=top_k, metadata_filter=metadata_filter)
    
    logger.info("retrieve_context: Found %d parent chunks", len(results))
    return results
