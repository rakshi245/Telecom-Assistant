import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
from utils.document_loader import list_documents
# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from orchestration.graph import create_graph
from utils.database import (
    get_customer_dashboard_data, 
    get_network_dashboard_data, 
    get_customer_by_email,
    get_all_support_tickets
)
from utils.document_loader import add_document_to_knowledge_base

# Page Config
st.set_page_config(page_title="Telecom Super-Agent", page_icon="📡", layout="wide")

# State Management
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "user_role" not in st.session_state: st.session_state.user_role = None # 'customer' or 'admin'
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "graph" not in st.session_state: st.session_state.graph = create_graph()

# --- HELPER FUNCTIONS ---
def process_query(query: str):
    user_id = st.session_state.get("customer_id", "CUST_001")
    initial_state = {
        "query": query,
        "customer_info": {"id": user_id},
        "classification": "",
        "intermediate_responses": {},
        "final_response": "",
        "chat_history": st.session_state.chat_history
    }
    result = st.session_state.graph.invoke(initial_state)
    return result["final_response"]

# --- SIDEBAR (Dual Login) ---
with st.sidebar:
    st.title("📡 Teleserve AI")
    
    if not st.session_state.authenticated:
        st.subheader("Login")
        login_mode = st.radio("Mode", ["Customer", "Admin"])
        
        if login_mode == "Customer":
            email = st.text_input("Email", value="sarah.j@example.com")
            if st.button("Login"):
                user = get_customer_by_email(email)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "customer"
                    st.session_state.customer_id = user['customer_id']
                    st.session_state.customer_name = user['name']
                    st.rerun()
                else:
                    st.error("Email not found.")
        
        else: # Admin Mode
            admin_pass = st.text_input("Admin Key", type="password")
            if st.button("Admin Login"):
                if admin_pass == "admin123": # Simple hardcoded check
                    st.session_state.authenticated = True
                    st.session_state.user_role = "admin"
                    st.rerun()
                else:
                    st.error("Invalid Key")

    else:
        # LOGGED IN SIDEBAR
        if st.session_state.user_role == "customer":
            st.success(f"👤 {st.session_state.customer_name}")
        else:
            st.warning("🛡️ Administrator Mode")
            
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.chat_history = []
            st.rerun()

# --- MAIN APP ---
if st.session_state.authenticated:
    
    # === CUSTOMER VIEW ===
    if st.session_state.user_role == "customer":
        tab1, tab2, tab3 = st.tabs(["💬 Chat Assistant", "📊 My Usage", "⚠️ Network Status"])

        with tab1:
            st.subheader("AI Support Assistant")
            for msg in st.session_state.chat_history:
                st.chat_message(msg["role"]).write(msg["content"])
            if prompt := st.chat_input("How can I help you today?"):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                st.chat_message("user").write(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("Processing..."):
                        response = process_query(prompt)
                        st.write(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})

        with tab2:
            st.subheader("Real-Time Usage")
            data = get_customer_dashboard_data(st.session_state.customer_id)
            if data:
                col1, col2, col3 = st.columns(3)
                col1.metric("Data Used", f"{data['data_used']} GB", "Limit: 100 GB")
                col2.metric("Voice", f"{data['voice_used']} Mins")
                col3.metric("SMS", f"{data['sms_used']}")
                st.info(f"Current Plan: **{data['plan_name']}**")

        with tab3:
            st.subheader("Network Status Map")
            incidents = get_network_dashboard_data()
            if not incidents.empty:
                st.dataframe(incidents)
            else:
                st.success("No active incidents.")

    # === ADMIN VIEW ===
    else:
        st.title("🛡️ Admin Dashboard")
        
        # ADDED "Network Monitoring" to tabs
        tab1, tab2, tab3 = st.tabs(["📚 Knowledge Base", "🎫 Support Tickets", "📡 Network Monitoring"])
        
        # --- TAB 1: KNOWLEDGE BASE ---
        with tab1:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Current Documents")
                st.markdown("These files are currently indexed in the AI's brain:")
                
                # CALL THE NEW FUNCTION
                docs_df = list_documents()
                
                if not docs_df.empty:
                    st.dataframe(docs_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No documents found in knowledge base.")

            with col2:
                st.subheader("Add New Content")
                st.markdown("Upload PDF or Text files to update the AI's knowledge.")
                
                uploaded_file = st.file_uploader("Choose a file", type=["txt", "md", "pdf"])
                if uploaded_file is not None:
                    if st.button("Process & Add", type="primary"):
                        with st.spinner("Indexing document..."):
                            success, msg = add_document_to_knowledge_base(uploaded_file)
                            if success:
                                st.success(msg)
                                st.rerun() # Refresh to show the new file in the list
                            else:
                                st.error(msg)
        
        # --- TAB 2: SUPPORT TICKETS ---
        with tab2:
            st.subheader("Active Support Tickets")
            tickets = get_all_support_tickets()
            
            if not tickets.empty:
                # Add filters
                status_filter = st.multiselect("Filter by Status", options=tickets["status"].unique(), default=tickets["status"].unique())
                filtered_tickets = tickets[tickets["status"].isin(status_filter)]
                st.dataframe(filtered_tickets, use_container_width=True, hide_index=True)
            else:
                st.success("No open tickets! Good job.")

        # --- TAB 3: NETWORK MONITORING (NEW) ---
        with tab3:
            st.subheader("Live Network Operations Center")
            
            # 1. Fetch Data from DB
            incidents = get_network_dashboard_data()
            
            # 2. Calculate Dynamic Metrics
            total_active = len(incidents)
            affected_regions = incidents['location'].nunique() if not incidents.empty else 0
            
            # Determine System Status based on data
            system_status = "Healthy 🟢"
            if not incidents.empty:
                if "Critical" in incidents['severity'].values:
                    system_status = "Critical 🔴"
                else:
                    system_status = "Degraded 🟠"
            
            # 3. Display Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Active Incidents", total_active)
            m2.metric("Affected Locations", affected_regions)
            m3.metric("Network Status", system_status)
            
            st.divider()
            
            # 4. Display Data Table
            if not incidents.empty:
                st.markdown("### 🚨 Active Incident Report")
                
                # Show key columns from the database
                display_df = incidents[[
                    'incident_id', 'location', 'severity', 
                    'description', 'affected_services', 'start_time'
                ]]
                
                st.dataframe(
                    display_df, 
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "start_time": st.column_config.DatetimeColumn("Reported At", format="D MMM, HH:mm"),
                        "severity": st.column_config.TextColumn(
                            "Severity",
                            help="Critical incidents require immediate attention"
                        )
                    }
                )
            else:
                st.success("✅ All Network Systems Operational. No records in 'network_incidents' table with status='Active'.")
            
else:
    st.title("Telecom Service Assistant")
    st.info("Please login from the sidebar.")