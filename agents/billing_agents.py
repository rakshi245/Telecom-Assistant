# agents/billing_agents.py
from crewai import Agent, Task, Crew, Process
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from config.config import Config
import os

os.environ["OPENAI_API_KEY"] = Config.OPENAI_API_KEY

# --- 1. Define the Custom Tool ---

class SQLQueryInput(BaseModel):
    """Input schema for the SQL tool."""
    query: str = Field(description="The SQL query to execute")

class BillingDatabaseTool(BaseTool):
    name: str = "Search Telecom Database"
    description: str = """
    Use this to query the telecom database. 
    Useful tables: 
    - 'customer_usage' (contains data_used_gb, minutes_used, sms_used)
    - 'service_plans' (contains monthly_cost, data_limit_gb, etc.)
    - 'customers' (contains current_plan_id)
    Input should be a valid SQL query.
    """
    args_schema: Type[BaseModel] = SQLQueryInput
    
    db_conn: SQLDatabase = Field(exclude=True) 

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str) -> str:
        """Execute the query against the database"""
        try:
            return self.db_conn.run(query)
        except Exception as e:
            return f"Error executing SQL: {e}"

def get_billing_tools():
    """Create the custom SQL tool for the agents to use"""
    db = SQLDatabase.from_uri(f"sqlite:///{Config.DB_PATH}")
    return [BillingDatabaseTool(db_conn=db)]

# --- 2. Process Function ---

def process_billing_query(query: str, customer_id: str = "CUST_001") -> str:
    """
    Orchestrates a CrewAI team to analyze billing issues.
    """
    print(f"   [CrewAI] Spawning Billing Agents for: '{query}'...")
    
    # Setup Tools & LLM
    billing_tools = get_billing_tools()
    llm = ChatOpenAI(model=Config.LLM_MODEL, temperature=0)
    
    # Define Agents with Smarter Backstories
    billing_specialist = Agent(
        role='Senior Billing Analyst',
        goal='Calculate bill amounts by joining usage and plan tables',
        backstory="""You are a forensic data analyst. 
        You know that there is NO single 'billing' table. 
        Instead, you calculate the bill by checking the customer's plan in the 'customers' table, 
        finding the cost in 'service_plans', and checking 'customer_usage' for any overages.
        You always verify table names before querying.""",
        tools=billing_tools,
        llm=llm,
        verbose=True
    )

    service_advisor = Agent(
        role='Customer Service Manager',
        goal='Explain the calculated bill to the customer',
        backstory="""You help customers understand their charges. 
        You take the technical breakdown from the Analyst (e.g., "Plan Cost + Overage") 
        and explain it simply (e.g., "Your base plan is $50, but you used extra data").""",
        llm=llm,
        verbose=True
    )

    # Define Tasks
    # Task 1: Smarter Analysis
    analysis_task = Task(
        description=f"""
        Investigate the billing query for customer '{customer_id}': "{query}"
        
        Steps:
        1. List the tables to confirm what is available (use sqlite_master).
        2. Find the customer's current plan_id from the 'customers' table.
        3. Get the monthly_cost for that plan from the 'service_plans' table.
        4. Check 'customer_usage' to see if they exceeded their limits (compare usage vs plan limits).
        5. Calculate the total estimated bill (Base Cost + any potential overages).
        """,
        agent=billing_specialist,
        expected_output="A breakdown containing: Plan Name, Base Cost, Usage Levels, and Estimated Total."
    )

    # Task 2: Write the response
    explain_task = Task(
        description=f"""
        Write a helpful response to the customer based on the Analyst's calculation.
        Explain WHY the bill is that amount (e.g., "You are on the Gold Plan which costs X...").
        If usage was high, mention that.
        """,
        agent=service_advisor,
        expected_output="A friendly paragraph explaining the bill logic to the user.",
        context=[analysis_task]
    )

    # Create Crew
    billing_crew = Crew(
        agents=[billing_specialist, service_advisor],
        tasks=[analysis_task, explain_task],
        process=Process.sequential,
        verbose=True
    )

    # Execute
    try:
        result = billing_crew.kickoff()
        return str(result)
    except Exception as e:
        print(f"Error in Billing Crew: {e}")
        return "I'm having trouble connecting to the billing system right now."