import sys
import os
from streamlit.web import cli as stcli

def main():
    """
    Main entry point for the Telecom Service Assistant.
    This wrapper allows running the app via 'python app.py'
    instead of 'streamlit run ui/streamlit_app.py'.
    """
    print("🚀 Starting Telecom Service Assistant...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "ui", "streamlit_app.py")
    
    sys.argv = ["streamlit", "run", script_path]
    
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()