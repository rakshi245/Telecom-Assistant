# agents/service_agents.py
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from config.config import Config
import os

# Ensure API key is set
os.environ["OPENAI_API_KEY"] = Config.OPENAI_API_KEY

def process_service_query(query: str, customer_id: str) -> str:
    """
    Uses a LangChain SQL Agent to query the telecom.db database.
    """
    try:
        # 1. Connect to the Database
        db = SQLDatabase.from_uri(f"sqlite:///{Config.DB_PATH}")
        
        # 2. Create the LLM
        llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=0
        )
        
        # 3. Create the SQL Agent
        agent_executor = create_sql_agent(
            llm=llm,
            db=db,
            agent_type="openai-tools",
            verbose=True
        )
        
        # 4. Define the Contextual Prompt
        # We explicitly tell the AI who the user is and how to find their plan.
        system_prefix = f"""
        You are a helpful telecom assistant.
        The user you are speaking with has customer_id: '{customer_id}'.
        
        Rules:
        1. If the user asks about "my plan", "current plan", or "account details":
           - First query the 'customers' table using customer_id='{customer_id}' to find their 'service_plan_id'.
           - Then query the 'service_plans' table with that id to retrieve the plan name, cost, and features.
        
        2. If the user asks for generic recommendations (e.g., "best plan for families"), just query the 'service_plans' table directly.
        
        3. Always mention the Plan Name and Monthly Cost in your answer.
        """
        
        print(f"   [LangChain] Querying DB for user {customer_id}: '{query}'...")
        
        # Run the agent with the injected prompt
        response = agent_executor.invoke(f"{system_prefix} User Query: {query}")
        
        return response["output"]

    except Exception as e:
        print(f"Error in Service Agent: {e}")
        return "I apologize, but I'm having trouble accessing the plan database right now."