"""Ingestion script for RAG Memory.

Parses markdown files, creates parent-child chunks, and indexes them
into the HybridStore. Preserves markdown tables intact.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from bioops.rag_memory.hybrid_store import HybridStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bioops_twin.rag.ingestion")

MANUALS_DIR = Path(__file__).parent.parent.parent / "data" / "manuals"

def chunk_markdown(text: str) -> list[str]:
    """Split markdown into logical parent sections based on headers."""
    # Split by H2 headers (##)
    sections = re.split(r"(?=\n## )", text)
    return [sec.strip() for sec in sections if sec.strip()]

def create_child_chunks(parent_text: str, chunk_size_words: int = 50) -> list[str]:
    """Create smaller child chunks from a parent text.
    
    Tries to keep lines together, especially for markdown tables.
    """
    lines = parent_text.split("\n")
    children = []
    current_child = []
    current_words = 0
    
    in_table = False
    
    for line in lines:
        words_in_line = len(line.split())
        
        # Check if we are in a markdown table
        if "|" in line and "-" in line and set(line.strip().replace("|", "").replace("-", "")) == set():
            in_table = True
        elif line.strip() == "":
            in_table = False
            
        current_child.append(line)
        current_words += words_in_line
        
        # If we reached the limit and we are not in the middle of a table, split
        if current_words >= chunk_size_words and not in_table:
            children.append("\n".join(current_child))
            current_child = []
            current_words = 0
            
    if current_child:
        children.append("\n".join(current_child))
        
    return children

def ingest_manuals() -> None:
    """Read all markdown manuals and ingest them into HybridStore."""
    store = HybridStore()
    
    if not MANUALS_DIR.exists():
        logger.warning(f"Manuals directory {MANUALS_DIR} does not exist. Nothing to ingest.")
        return
        
    for md_file in MANUALS_DIR.glob("*.md"):
        logger.info(f"Processing {md_file.name}...")
        
        # Infer equipment from filename (e.g. cent-01_calibration.md)
        filename_parts = md_file.stem.split("_")
        equipment_id = filename_parts[0].upper()
        manual_type = filename_parts[1] if len(filename_parts) > 1 else "general"
        
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Parent chunks
        parent_sections = chunk_markdown(content)
        
        for i, parent_text in enumerate(parent_sections):
            parent_id = f"{md_file.stem}_sec_{i}"
            
            # Child chunks
            children = create_child_chunks(parent_text)
            
            # Metadata
            metadata = {
                "equipment": equipment_id,
                "manual_type": manual_type,
                "source": md_file.name
            }
            
            store.add_documents(
                parent_id=parent_id,
                parent_text=parent_text,
                children=children,
                metadata=metadata
            )
            
    logger.info("Ingestion complete.")

if __name__ == "__main__":
    ingest_manuals()
