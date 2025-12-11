# orchestration/graph.py
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from agents.knowledge_agents import process_knowledge_query
from orchestration.state import TelecomAssistantState
from agents.service_agents import process_service_query
from agents.billing_agents import process_billing_query
from agents.network_agents import process_network_query
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config.config import Config


# --- 1. CLASSIFICATION NODE ---
def classify_query(state: TelecomAssistantState) -> TelecomAssistantState:
    query = state["query"].lower().strip()
    
    # 1. Edge Case: Empty Query
    if not query:
        return {**state, "classification": "general"}
        
    classification = "general" 

    # Check for "Complex" queries (referencing multiple topics)
    # If user mentions both "bill" and "network", we route to general to ask for clarification
    if any(w in query for w in ["bill", "payment"]) and any(w in query for w in ["network", "slow", "internet"]):
        classification = "general"

    # Billing
    elif any(w in query for w in ["bill", "charge", "price", "cost", "invoice", "payment", "top-up", "balance", "usage"]):
        classification = "billing"
    
    # Network
    elif any(w in query for w in ["internet", "slow", "down", "speed", "signal", "coverage", "no service", "latency", "outage"]):
        classification = "network"
    
    # Service/Sales
    elif any(w in query for w in ["plan", "recommend", "buy", "purchase", "upgrade", "new connection", "sim", "prepaid", "postpaid"]):
        classification = "service"
    
    # Technical/Knowledge
    elif any(w in query for w in ["how to", "how do", "set up", "setup", "configure", "apn", "manual", "guide", "what is", "volte", "activate", "promo", "code", "offer"]):
        classification = "knowledge"

    print(f"--- ROUTER DECISION: {classification.upper()} ---")
    return {**state, "classification": classification}

def general_node(state: TelecomAssistantState) -> TelecomAssistantState:
    """
    Handles fallback, chit-chat, jokes, and complex queries.
    """
    print("--> Entering General Node (Fallback)")
    query = state["query"]
    
    # 1. NEW LOGIC: Use LLM instead of hardcoded string
    try:
        llm = ChatOpenAI(model=Config.LLM_MODEL, temperature=0.7)
        
        messages = [
            SystemMessage(content="""
            You are a polite Telecom Assistant.
            - If the user asks for a joke, tell a telecom-related joke.
            - If the user asks about TWO topics at once (e.g., "Bill and Network"), politely ask them to focus on one at a time so you can connect them to the right department.
            - If it's a greeting, say hello and list your capabilities (Billing, Network, Plans, Tech Support).
            - Do not try to answer technical questions yourself; just guide them.
            """),
            HumanMessage(content=query)
        ]
        
        # 2. GENERATE RESPONSE
        response = llm.invoke(messages).content
        return {**state, "intermediate_responses": {"general": response}}
        
    except Exception as e:
        # Fallback only if LLM fails
        return {**state, "intermediate_responses": {"general": "I'm here to help with Billing, Network, or Plans."}}
    

# --- 2. ROUTING LOGIC ---
def route_query(state: TelecomAssistantState) -> str:
    """Returns the name of the next node to visit"""
    return state["classification"]

# --- 3. SPECIALIST NODES (MOCKS) ---
# We will replace these with real AI Agents in the next phase.

def billing_node(state: TelecomAssistantState) -> TelecomAssistantState:
    print("--> Entering Billing Node (CrewAI)")
    
    query = state["query"]
    # We simulate a logged-in user (CUST_001) for this demo
    # In the real app, this comes from state["customer_info"]
    customer_id = "CUST_001" 
    
    # CALL THE REAL CREW
    response = process_billing_query(query, customer_id)
    
    return {**state, "intermediate_responses": {"billing": response}}

def network_node(state: TelecomAssistantState) -> TelecomAssistantState:
    print("--> Entering Network Node (AutoGen)")
    
    query = state["query"]
    # CALL THE REAL AGENT
    response = process_network_query(query)
    
    return {**state, "intermediate_responses": {"network": response}}

def service_node(state: TelecomAssistantState) -> TelecomAssistantState:
    print("--> Entering Service Node (LangChain)")
    
    query = state["query"]
    
    # Get the Customer ID from state, default to CUST_001 if missing
    customer_info = state.get("customer_info", {})
    customer_id = customer_info.get("id", "CUST_001")
    
    # CALL THE REAL AGENT WITH THE ID
    response = process_service_query(query, customer_id)
    
    return {**state, "intermediate_responses": {"service": response}}

def knowledge_node(state: TelecomAssistantState) -> TelecomAssistantState:
    print("--> Entering Knowledge Node (LlamaIndex)")
    
    query = state["query"]
    # CALL THE REAL AGENT
    response = process_knowledge_query(query)
    
    return {**state, "intermediate_responses": {"knowledge": response}}


# --- 4. RESPONSE FORMULATION ---
def formulate_response(state: TelecomAssistantState) -> TelecomAssistantState:
    """Combines intermediate outputs into a final string"""
    # Grab the last added response
    responses = state["intermediate_responses"]
    final_text = list(responses.values())[-1]
    return {**state, "final_response": final_text}

# --- 5. GRAPH CONSTRUCTION ---
def create_graph():
    workflow = StateGraph(TelecomAssistantState)

    # Add Nodes
    workflow.add_node("classify_query", classify_query)
    workflow.add_node("billing", billing_node)
    workflow.add_node("network", network_node)
    workflow.add_node("service", service_node)
    workflow.add_node("knowledge", knowledge_node)
    workflow.add_node("general", general_node)
    workflow.add_node("formulate_response", formulate_response)

    # Set Entry Point
    workflow.set_entry_point("classify_query")

    # Add Conditional Routing
    workflow.add_conditional_edges(
        "classify_query",
        route_query,
        {
            "billing": "billing",
            "network": "network",
            "service": "service",
            "knowledge": "knowledge",
            "general": "general"
        }
    )

    # All nodes go to response formulation
    workflow.add_edge("billing", "formulate_response")
    workflow.add_edge("network", "formulate_response")
    workflow.add_edge("service", "formulate_response")
    workflow.add_edge("knowledge", "formulate_response")
    workflow.add_edge("general", "formulate_response")
    
    # End
    workflow.add_edge("formulate_response", END)

    return workflow.compile()