# utils/database.py
import sqlite3
import pandas as pd
from config.config import Config

def get_db_connection():
    """Create a connection to the SQLite database"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def inspect_database():
    """Helper to print table names and schema for debugging"""
    conn = get_db_connection()
    if conn:
        print("\n=== Database Inspection ===")
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            
            # Get columns for this table
            df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 1", conn)
            print(f"Columns: {list(df.columns)}")
        
        conn.close()
        print("\n===========================")


# ... existing imports and code ...
def get_customer_dashboard_data(customer_id="CUST_001"):
    """Fetch live usage and plan details for the dashboard"""
    conn = get_db_connection()
    if not conn: return None
    
    # 1. Get Usage
    usage_df = pd.read_sql(
        f"SELECT * FROM customer_usage WHERE customer_id = '{customer_id}'", conn
    )
    
    # 2. Get Customer's Plan ID (CORRECTED COLUMN NAME HERE)
    cust_df = pd.read_sql(
        f"SELECT service_plan_id FROM customers WHERE customer_id = '{customer_id}'", conn
    )
    
    # Extract the ID safely
    plan_id = cust_df.iloc[0]['service_plan_id'] if not cust_df.empty else None
    
    # 3. Get Plan Name
    plan_name = "Unknown"
    if plan_id:
        plan_df = pd.read_sql(
            f"SELECT name FROM service_plans WHERE plan_id = '{plan_id}'", conn
        )
        if not plan_df.empty:
            plan_name = plan_df.iloc[0]['name']

    conn.close()
    
    if usage_df.empty: return None
    
    row = usage_df.iloc[0]
    return {
        "plan_name": plan_name,
        "data_used": row.get('data_used_gb', 0),
        "voice_used": row.get('voice_minutes_used', 0), # Corrected based on your schema
        "sms_used": row.get('sms_count_used', 0)        # Corrected based on your schema
    }

def get_network_dashboard_data():
    """Fetch all active incidents"""
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    
    df = pd.read_sql("SELECT * FROM network_incidents WHERE status = 'Active'", conn)
    conn.close()
    return df

def get_customer_by_email(email: str):
    """
    Validate email and return customer details.
    """
    conn = get_db_connection()
    if not conn: return None
    
    try:
        # Sanitize and query
        clean_email = email.strip()
        query = f"SELECT customer_id, name FROM customers WHERE email = '{clean_email}'"
        df = pd.read_sql(query, conn)
        conn.close()
        
        if df.empty:
            return None
            
        return df.iloc[0].to_dict() # Returns {'customer_id': '...', 'name': '...'}
        
    except Exception as e:
        print(f"Login Error: {e}")
        return None

# ... existing imports ...

def get_all_support_tickets():
    """Fetch all open tickets for the Admin Dashboard"""
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    
    # Get tickets joined with customer names
    query = """
    SELECT t.ticket_id, c.name as customer_name, t.issue_category, 
           t.status, t.priority, t.creation_time
    FROM support_tickets t
    JOIN customers c ON t.customer_id = c.customer_id
    WHERE t.status != 'Closed'
    ORDER BY t.creation_time DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


if __name__ == "__main__":
    # If run directly, inspect the DB
    inspect_database()