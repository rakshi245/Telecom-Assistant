# orchestration/state.py
from typing import TypedDict, Dict, Any, List, Optional

class TelecomAssistantState(TypedDict):
    """
    Represents the state of the telecom assistant workflow.
    This dictionary is passed between all nodes in the graph.
    """
    query: str                          # The user's original question
    customer_info: Dict[str, Any]       # Email, ID, etc.
    classification: str                 # 'billing', 'network', 'service', 'general'
    intermediate_responses: Dict[str, Any] # Storage for agent outputs
    final_response: str                 # The answer shown to the user
    chat_history: List[Dict[str, str]]  # Previous conversation context