# agents/knowledge_agents.py
from utils.document_loader import get_knowledge_index

def process_knowledge_query(query: str) -> str:
    try:
        # Load index
        index = get_knowledge_index()
        if not index:
            return "Knowledge base unavailable."
        
        # INCREASED TOP_K TO 5
        query_engine = index.as_query_engine(similarity_top_k=5)
        
        print(f"   [LlamaIndex] Searching documents for: '{query}'...")
        response = query_engine.query(query)
        
        # Check if response is empty
        if str(response).strip() == "Empty Response":
            return "I couldn't find that specific information in my documents."
            
        return str(response)
        
    except Exception as e:
        print(f"Error: {e}")
        return "Error searching documentation."