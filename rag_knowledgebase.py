"""
RAG Knowledge Base Integration
================================

This module provides RAG (Retrieval-Augmented Generation) capabilities to enhance
your social media posting pipeline with context from a knowledge base.

Features:
- Hybrid search (BM25 + semantic embeddings)
- Automatic document chunking
- Integration with Notion API for dynamic knowledge base
- SQLite-based storage with FTS5 and vector search
"""

import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import sqlite_vec
from fastembed import TextEmbedding

from config import NOTION_API_KEY, NOTION_PAGE_ID
from notion import get_page_content


# ========================
# Configuration
# ========================

DATABASE_PATH = Path("knowledge_base.db")
EMBEDDING_MODEL = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
EMBEDDING_DIM = 384  # Dimension for BAAI/bge-small-en-v1.5


# ========================
# Database Initialization
# ========================

def init_database(db_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """
    Initialize SQLite database with:
    - Metadata table for document content
    - Vector table for semantic search (sqlite-vec)
    - FTS5 table for keyword search (BM25)
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Load sqlite-vec extension
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)

    cursor = conn.cursor()

    # Metadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS embeddings_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,
            source_id TEXT,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Vector table using sqlite-vec
    cursor.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_embeddings USING vec0(
            embedding float[{EMBEDDING_DIM}] distance_metric=cosine
        )
    """)

    # FTS5 virtual table for BM25 keyword search
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS embeddings_fts USING fts5(
            content,
            source_type,
            source_id,
            content='embeddings_meta',
            content_rowid='id'
        )
    """)

    # Triggers to keep FTS5 in sync
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS embeddings_ai AFTER INSERT ON embeddings_meta BEGIN
            INSERT INTO embeddings_fts(rowid, content, source_type, source_id)
            VALUES (new.id, new.content, new.source_type, new.source_id);
        END
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS embeddings_ad AFTER DELETE ON embeddings_meta BEGIN
            INSERT INTO embeddings_fts(embeddings_fts, rowid, content, source_type, source_id)
            VALUES ('delete', old.id, old.content, old.source_type, old.source_id);
        END
    """)

    conn.commit()
    return conn


# ========================
# Document Chunking
# ========================

def chunk_document(content: str, source_id: str, chunk_size: int = 800) -> list[dict]:
    """
    Chunk document by paragraphs with a target size.
    
    This strategy works well for Notion pages that might not have consistent headers.
    
    Args:
        content: The full document text
        source_id: Identifier for the source (e.g., Notion page ID)
        chunk_size: Target size for each chunk in characters
        
    Returns:
        List of chunk dictionaries with content and metadata
    """
    # Split by double newlines (paragraphs)
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para_size = len(para)
        
        # If adding this paragraph exceeds chunk_size, save current chunk
        if current_size + para_size > chunk_size and current_chunk:
            chunk_content = '\n\n'.join(current_chunk)
            chunks.append({
                "content": chunk_content,
                "source_type": "notion",
                "source_id": source_id,
                "metadata": {
                    "char_count": len(chunk_content),
                    "created_at": datetime.now().isoformat()
                }
            })
            current_chunk = []
            current_size = 0
        
        current_chunk.append(para)
        current_size += para_size
    
    # Add remaining content
    if current_chunk:
        chunk_content = '\n\n'.join(current_chunk)
        chunks.append({
            "content": chunk_content,
            "source_type": "notion",
            "source_id": source_id,
            "metadata": {
                "char_count": len(chunk_content),
                "created_at": datetime.now().isoformat()
            }
        })
    
    return chunks


def chunk_by_headers(content: str, source_id: str) -> list[dict]:
    """
    Alternative chunking strategy: split by markdown headers (##).
    
    Use this if your Notion pages have consistent header structure.
    """
    # Extract document title
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    doc_title = title_match.group(1) if title_match else "Untitled"

    # Split on ## headers
    sections = re.split(r'(?=^##\s+)', content, flags=re.MULTILINE)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract section title
        section_title_match = re.search(r'^##\s+(.+)$', section, re.MULTILINE)
        section_title = section_title_match.group(1) if section_title_match else "Introduction"

        # Build chunk with context
        chunk_content = f"# {doc_title}\n\n{section}"

        chunks.append({
            "content": chunk_content,
            "source_type": "notion",
            "source_id": source_id,
            "metadata": {
                "doc_title": doc_title,
                "section_title": section_title,
                "created_at": datetime.now().isoformat()
            }
        })

    return chunks


# ========================
# Embeddings
# ========================

def generate_embedding(text: str) -> np.ndarray:
    """Generate embedding for a single text using FastEmbed."""
    embedding = list(EMBEDDING_MODEL.embed([text]))[0]
    return np.array(embedding, dtype=np.float32)


def generate_embeddings_batch(texts: list[str]) -> list[np.ndarray]:
    """Generate embeddings for multiple texts efficiently."""
    embeddings = list(EMBEDDING_MODEL.embed(texts))
    return [np.array(emb, dtype=np.float32) for emb in embeddings]


# ========================
# Storage Operations
# ========================

def store_chunks(conn: sqlite3.Connection, chunks: list[dict]) -> None:
    """
    Store chunks with their embeddings in the database.
    
    This function:
    1. Generates embeddings for all chunks
    2. Stores metadata in embeddings_meta
    3. Stores vectors in vec_embeddings
    4. FTS5 is auto-updated via triggers
    """
    if not chunks:
        return
    
    cursor = conn.cursor()
    
    # Generate embeddings
    texts = [chunk["content"] for chunk in chunks]
    embeddings = generate_embeddings_batch(texts)
    
    for chunk, embedding in zip(chunks, embeddings):
        # Insert metadata
        cursor.execute("""
            INSERT INTO embeddings_meta (source_type, source_id, content, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            chunk["source_type"],
            chunk["source_id"],
            chunk["content"],
            json.dumps(chunk.get("metadata", {}))
        ))
        
        meta_id = cursor.lastrowid
        
        # Insert vector with matching rowid
        cursor.execute("""
            INSERT INTO vec_embeddings (rowid, embedding)
            VALUES (?, ?)
        """, (meta_id, embedding.tobytes()))
    
    conn.commit()


def clear_source(conn: sqlite3.Connection, source_id: str) -> None:
    """Remove all chunks from a specific source (e.g., before re-indexing)."""
    cursor = conn.cursor()
    
    # Get IDs to delete
    cursor.execute("SELECT id FROM embeddings_meta WHERE source_id = ?", (source_id,))
    ids_to_delete = [row[0] for row in cursor.fetchall()]
    
    if not ids_to_delete:
        return
    
    # Delete from vec_embeddings
    placeholders = ','.join('?' * len(ids_to_delete))
    cursor.execute(f"DELETE FROM vec_embeddings WHERE rowid IN ({placeholders})", ids_to_delete)
    
    # Delete from embeddings_meta (triggers will handle FTS5)
    cursor.execute(f"DELETE FROM embeddings_meta WHERE id IN ({placeholders})", ids_to_delete)
    
    conn.commit()


# ========================
# Search Operations
# ========================

def bm25_search(conn: sqlite3.Connection, query: str, top_k: int = 10) -> list[dict]:
    """
    Perform BM25 keyword search using FTS5.
    
    Returns results with negative BM25 scores (more negative = better).
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT
            m.id,
            m.content,
            m.source_type,
            m.source_id,
            m.metadata,
            -bm25(embeddings_fts) as bm25_score
        FROM embeddings_fts
        JOIN embeddings_meta m ON m.id = embeddings_fts.rowid
        WHERE embeddings_fts MATCH ?
        ORDER BY bm25_score DESC
        LIMIT ?
    """, (query, top_k))
    
    return [dict(row) for row in cursor.fetchall()]


def semantic_search(conn: sqlite3.Connection, query_embedding: np.ndarray, top_k: int = 10) -> list[dict]:
    """
    Perform semantic search using cosine similarity.
    
    Returns results with cosine distance (lower = more similar).
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT
            m.id,
            m.content,
            m.source_type,
            m.source_id,
            m.metadata,
            distance
        FROM vec_embeddings v
        JOIN embeddings_meta m ON m.id = v.rowid
        WHERE embedding MATCH ?
        AND k = ?
        ORDER BY distance
    """, (query_embedding.tobytes(), top_k))
    
    return [dict(row) for row in cursor.fetchall()]


def hybrid_search(
    conn: sqlite3.Connection,
    query: str,
    query_embedding: np.ndarray,
    top_k: int = 10,
    bm25_weight: float = 0.3,
    semantic_weight: float = 0.7
) -> list[dict]:
    """
    Combine BM25 and semantic search using weighted scoring.
    
    Args:
        conn: Database connection
        query: Search query text
        query_embedding: Pre-computed query embedding
        top_k: Number of results to return
        bm25_weight: Weight for BM25 score (0-1)
        semantic_weight: Weight for semantic score (0-1)
        
    Returns:
        List of results sorted by combined score
    """
    # Get results from both methods
    bm25_results = bm25_search(conn, query, top_k=top_k * 2)
    semantic_results = semantic_search(conn, query_embedding, top_k=top_k * 2)
    
    # Normalize scores to 0-1 range
    if bm25_results:
        max_bm25 = max(r['bm25_score'] for r in bm25_results)
        min_bm25 = min(r['bm25_score'] for r in bm25_results)
        bm25_range = max_bm25 - min_bm25 if max_bm25 != min_bm25 else 1
        
        for r in bm25_results:
            r['bm25_normalized'] = (r['bm25_score'] - min_bm25) / bm25_range
    
    if semantic_results:
        max_dist = max(r['distance'] for r in semantic_results)
        min_dist = min(r['distance'] for r in semantic_results)
        dist_range = max_dist - min_dist if max_dist != min_dist else 1
        
        for r in semantic_results:
            # Invert distance to similarity (1 - normalized_distance)
            r['semantic_normalized'] = 1 - ((r['distance'] - min_dist) / dist_range)
    
    # Merge results by ID
    merged = {}
    for r in bm25_results:
        merged[r['id']] = {
            **r,
            'bm25_score': r.get('bm25_normalized', 0),
            'semantic_score': 0
        }
    
    for r in semantic_results:
        if r['id'] in merged:
            merged[r['id']]['semantic_score'] = r.get('semantic_normalized', 0)
        else:
            merged[r['id']] = {
                **r,
                'bm25_score': 0,
                'semantic_score': r.get('semantic_normalized', 0)
            }
    
    # Calculate final scores
    for doc_id, result in merged.items():
        result['final_score'] = (
            bm25_weight * result['bm25_score'] +
            semantic_weight * result['semantic_score']
        )
    
    # Sort and return top-k
    sorted_results = sorted(
        merged.values(),
        key=lambda x: x['final_score'],
        reverse=True
    )
    
    return sorted_results[:top_k]


# ========================
# High-Level Functions
# ========================

def format_context_for_prompt(results: list[dict], max_chars: int = 4000) -> str:
    """
    Format search results into context string for LLM prompt.
    
    Limits total character count to stay within token limits.
    """
    if not results:
        return "No relevant context found."
    
    context_parts = []
    chars_used = 0
    
    for i, result in enumerate(results, 1):
        header = f"[{i}. {result['source_type']}] (score: {result['final_score']:.2f})"
        content = result["content"]
        
        available = max_chars - chars_used - len(header) - 10
        if available <= 100:
            break
        
        if len(content) > available:
            content = content[:available - 3] + "..."
        
        entry = f"{header}\n{content}\n"
        context_parts.append(entry)
        chars_used += len(entry)
    
    return "\n".join(context_parts)


def retrieve_context(
    conn: sqlite3.Connection,
    query: str,
    top_k: int = 5,
    max_chars: int = 4000
) -> tuple[str, list[dict]]:
    """
    High-level function to retrieve and format context for RAG.
    
    Args:
        conn: Database connection
        query: Search query
        top_k: Number of chunks to retrieve
        max_chars: Maximum characters in formatted context
        
    Returns:
        (formatted_context, raw_results)
    """
    print(f"\n{'='*60}")
    print(f"🔍 RAG RETRIEVAL PROCESS")
    print(f"{'='*60}")
    print(f"Query: '{query}'")
    print(f"Retrieving top {top_k} chunks...\n")
    
    # Generate query embedding
    print(f"🧮 Generating query embedding...")
    query_embedding = generate_embedding(query)
    print(f"✓ Query embedded (384 dimensions)\n")
    
    # Perform hybrid search
    print(f"🔎 Performing hybrid search (BM25 + Semantic)...")
    print(f"   - BM25 weight: 30% (keyword matching)")
    print(f"   - Semantic weight: 70% (meaning matching)")
    results = hybrid_search(conn, query, query_embedding, top_k=top_k)
    print(f"✓ Found {len(results)} relevant chunks\n")
    
    # Show retrieval results
    if results:
        print(f"📊 RETRIEVAL RESULTS:")
        for i, result in enumerate(results, 1):
            preview = result['content'][:80].replace('\n', ' ')
            bm25 = result.get('bm25_score', 0)
            semantic = result.get('semantic_score', 0)
            final = result['final_score']
            print(f"   {i}. Score: {final:.3f} (BM25: {bm25:.2f}, Semantic: {semantic:.2f})")
            print(f"      Preview: {preview}...")
            print()
    
    # Format for prompt
    print(f"📝 Formatting context for LLM prompt...")
    formatted = format_context_for_prompt(results, max_chars=max_chars)
    print(f"✓ Context formatted ({len(formatted)} chars, max: {max_chars})")
    print(f"{'='*60}\n")
    
    return formatted, results


# ========================
# Notion Integration
# ========================

def sync_notion_page(conn: sqlite3.Connection, page_id: str = None) -> int:
    """
    Fetch content from Notion and update the knowledge base.
    
    Args:
        conn: Database connection
        page_id: Notion page ID (defaults to NOTION_PAGE_ID from config)
        
    Returns:
        Number of chunks stored
    """
    if page_id is None:
        page_id = NOTION_PAGE_ID
    
    if not page_id:
        raise ValueError("No Notion page ID provided")
    
    print(f"\n{'='*60}")
    print(f"📥 SYNCING NOTION PAGE TO KNOWLEDGE BASE")
    print(f"{'='*60}")
    print(f"Page ID: {page_id}")
    
    # Fetch content
    content = get_page_content(page_id)
    print(f"✓ Fetched {len(content)} characters from Notion")
    
    # Clear existing content from this source
    clear_source(conn, page_id)
    print(f"✓ Cleared existing chunks for page {page_id}")
    
    # Chunk the content
    print(f"\n🔪 CHUNKING DOCUMENT...")
    print(f"   Strategy: Paragraph-based chunking (target: 800 chars/chunk)")
    chunks = chunk_document(content, page_id)
    print(f"✓ Created {len(chunks)} chunks")
    
    # Show chunk preview
    if chunks:
        print(f"\n📄 Chunk Preview:")
        for i, chunk in enumerate(chunks[:3], 1):
            preview = chunk['content'][:100].replace('\n', ' ')
            print(f"   Chunk {i}: {preview}... ({len(chunk['content'])} chars)")
        if len(chunks) > 3:
            print(f"   ... and {len(chunks) - 3} more chunks")
    
    # Store with embeddings
    print(f"\n🧮 GENERATING EMBEDDINGS...")
    print(f"   Model: BAAI/bge-small-en-v1.5 (384 dimensions)")
    store_chunks(conn, chunks)
    print(f"✓ Stored {len(chunks)} chunks with embeddings in database")
    print(f"{'='*60}\n")
    
    return len(chunks)


def initialize_knowledge_base(notion_page_ids: list[str] = None) -> sqlite3.Connection:
    """
    Initialize the knowledge base and optionally sync Notion pages.
    
    Args:
        notion_page_ids: List of Notion page IDs to sync (optional)
        
    Returns:
        Database connection
    """
    conn = init_database()
    print(f"✓ Database initialized at {DATABASE_PATH}")
    
    if notion_page_ids:
        for page_id in notion_page_ids:
            try:
                sync_notion_page(conn, page_id)
            except Exception as e:
                print(f"✗ Failed to sync page {page_id}: {e}")
    
    return conn


# ========================
# Example Usage
# ========================

if __name__ == "__main__":
    """
    Example: Initialize knowledge base and test retrieval
    """
    # Initialize database and sync Notion
    db = initialize_knowledge_base([NOTION_PAGE_ID])
    
    # Test retrieval
    test_query = "AI consulting services"
    context, results = retrieve_context(db, test_query, top_k=3)
    
    print("\n" + "="*60)
    print(f"Query: {test_query}")
    print("="*60)
    print("\nRetrieved Context:")
    print(context)
    
    # Close connection
    db.close()