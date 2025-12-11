# agents/network_agents.py
import autogen
from config.config import Config
from utils.database import get_db_connection
from utils.document_loader import get_knowledge_index
import pandas as pd
import os

os.environ["OPENAI_API_KEY"] = Config.OPENAI_API_KEY

# --- 1. Define Tools for AutoGen ---

def check_network_status(region: str) -> str:
    """
    Checks the 'network_incidents' table in SQL for any reported outages 
    in a specific region (e.g., 'Mumbai', 'Delhi').
    """
    try:
        conn = get_db_connection()
        # Sanitize input to prevent basic SQL injection issues in this demo
        clean_region = region.replace("'", "").strip()
        query = f"SELECT * FROM network_incidents WHERE location LIKE '%{clean_region}%' AND status = 'Active'"
        df = pd.read_sql(query, conn)
        conn.close()
        
        if df.empty:
            return f"No active network incidents reported in {clean_region}. The tower status is normal."
        else:
            return f"ALERT: Found active incidents in {clean_region}: \n{df.to_string()}"
    except Exception as e:
        return f"Error checking network status: {e}"

def search_troubleshooting_guide(issue: str) -> str:
    """
    Searches the technical support manuals for troubleshooting steps.
    """
    try:
        index = get_knowledge_index()
        query_engine = index.as_query_engine()
        response = query_engine.query(f"Troubleshooting steps for: {issue}")
        return str(response)
    except Exception as e:
        return "Manual unavailable."

# --- 2. Configure Agents ---

def process_network_query(query: str) -> str:
    print(f"   [AutoGen] Starting Group Chat for: '{query}'...")

    # Configuration for GPT-4o
    config_list = [
        {
            "model": "gpt-4o", 
            "api_key": Config.OPENAI_API_KEY
        }
    ]
    
    llm_config = {
        "config_list": config_list,
        "temperature": 0,
    }

    # Agent 1: The User Proxy (Represents the human/system interaction)
    user_proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config=False,
    )

    # Agent 2: The Network Engineer (Checks the Database)
    engineer = autogen.AssistantAgent(
        name="Network_Engineer",
        llm_config=llm_config,
        system_message="""
        You are a Level 2 Network Engineer.
        Your job is to FIRST check if there is a known outage in the user's region using 'check_network_status'.
        If there is an outage, inform the team.
        If there is NO outage, ask the Support Specialist to provide device troubleshooting steps.
        """
    )

    # Agent 3: Support Specialist (Reads the Manuals)
    support = autogen.AssistantAgent(
        name="Support_Specialist",
        llm_config=llm_config,
        system_message="""
        You are a Customer Support Specialist.
        If the Engineer says the network is fine, you must find troubleshooting steps for the user's device.
        Use 'search_troubleshooting_guide' to find the solution.
        Summarize the steps clearly for the user.
        """
    )

    # Register Tools (UPDATED SYNTAX HERE)
    autogen.register_function(
        check_network_status,
        caller=engineer,
        executor=user_proxy,
        name="check_network_status",
        description="Check for network outages in a region"
    )

    autogen.register_function(
        search_troubleshooting_guide,
        caller=support,
        executor=user_proxy,
        name="search_troubleshooting_guide",
        description="Search manual for troubleshooting steps"
    )

    # --- 3. Start the Group Chat ---
    
    groupchat = autogen.GroupChat(
        agents=[user_proxy, engineer, support], 
        messages=[], 
        max_round=6
    )
    
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Start the conversation
    user_proxy.initiate_chat(
        manager, 
        message=f"Customer Issue: {query}. \nFirst check for outages, then if needed provide troubleshooting steps. Return 'TERMINATE' when you have a final answer."
    )

    # Extract the final helpful response from history
    for message in reversed(groupchat.messages):
        content = message["content"]
        if content and "TERMINATE" not in content and message["name"] != "User_Proxy":
            return content

    return "I couldn't generate a complete network diagnosis."