# test_routing.py
from orchestration.graph import create_graph

def test_queries():
    app = create_graph()
    
    test_inputs = [
        "Why is my bill so high?",          # Should go to Billing
        "My internet is very slow",         # Should go to Network
        "I want to buy a new family plan",  # Should go to Service
        "How do I set up APN settings?",    # Should go to Knowledge
        "Hello there"                       # Should go to General
    ]
    
    print("=== STARTING ROUTING TEST ===\n")
    
    for query in test_inputs:
        print(f"User: {query}")
        state = {
            "query": query,
            "customer_info": {},
            "classification": "",
            "intermediate_responses": {},
            "final_response": "",
            "chat_history": []
        }
        
        # Run the graph
        result = app.invoke(state)
        
        print(f"Final Response: {result['final_response']}")
        print("-" * 30)

if __name__ == "__main__":
    test_queries()