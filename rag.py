from rag_knowledgebase import initialize_knowledge_base, sync_notion_page
from config import NOTION_PAGE_ID


def setup_knowledge_base():
    """
    Initialize the knowledge base and sync Notion content.
    Run this script before using RAG for the first time.
    """
    print("🚀 Setting up RAG knowledge base\n")
    
    # Initialize database
    print("Step 1: Initializing database...")
    db = initialize_knowledge_base()
    print("✓ Database created\n")
    
    # Sync Notion page
    print("Step 2: Syncing Notion content...")
    if NOTION_PAGE_ID:
        num_chunks = sync_notion_page(db, NOTION_PAGE_ID)
        print(f"✓ Synced {num_chunks} chunks from Notion\n")
    else:
        print("⚠️  No NOTION_PAGE_ID found in config. Skipping Notion sync.")
        print("   You can add pages later using sync_notion_page(db, page_id)\n")
    
    # Test retrieval
    if NOTION_PAGE_ID:
        print("Step 3: Testing retrieval...")
        from rag_knowledgebase import retrieve_context
        
        test_query = "main topic"
        context, results = retrieve_context(db, test_query, top_k=3)
        
        print(f"✓ Retrieved {len(results)} results for query: '{test_query}'")
        if results:
            print(f"  Top result score: {results[0]['final_score']:.2f}")
    
    db.close()
    
    print("\n✅ Knowledge base setup complete!")
    print("You can now run main_rag.py with use_rag=True")


if __name__ == "__main__":
    setup_knowledge_base()