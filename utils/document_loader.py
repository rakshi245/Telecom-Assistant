# utils/document_loader.py
import os
import shutil
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from config.config import Config

# Ensure OpenAI key is loaded
os.environ["OPENAI_API_KEY"] = Config.OPENAI_API_KEY

def get_knowledge_index(rebuild=False):
    """
    Build or Load the Vector Index.
    If rebuild=True, it deletes the existing index and creates a fresh one.
    """
   
    # 1. Force Rebuild: Delete existing vector store if requested
    if rebuild and os.path.exists(Config.VECTOR_STORE_DIR):
        print("Rebuilding index from scratch...")
        shutil.rmtree(Config.VECTOR_STORE_DIR)

    # 2. Try to load existing index (Fast Path)
    if os.path.exists(Config.VECTOR_STORE_DIR):
        try:
            storage_context = StorageContext.from_defaults(persist_dir=Config.VECTOR_STORE_DIR)
            return load_index_from_storage(storage_context)
        except Exception as e:
            print(f"Index corrupt or failed to load. Rebuilding... ({e})")

    # 3. Build new index (Slow Path - reads all .txt files)
    print(f"Building index from documents in: {Config.DOCS_DIR}")
    if not os.path.exists(Config.DOCS_DIR):
        os.makedirs(Config.DOCS_DIR)
        return None # Return None if no folder

    # Check if directory is empty
    if not os.listdir(Config.DOCS_DIR):
        print("No documents found to index.")
        return None

    documents = SimpleDirectoryReader(Config.DOCS_DIR).load_data()
    print(f"Loaded {len(documents)} document chunks.")

    index = VectorStoreIndex.from_documents(documents)
    
    # 4. Save to disk
    index.storage_context.persist(persist_dir=Config.VECTOR_STORE_DIR)
    print(f"✅ Index saved to {Config.VECTOR_STORE_DIR}")
    
    return index

def add_document_to_knowledge_base(uploaded_file):
    """
    Saves a file and forces the index to rebuild.
    """
    try:
        # 1. Save the file
        save_path = os.path.join(Config.DOCS_DIR, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        print(f"Saved new document: {save_path}")
        
        # 2. FORCE REBUILD so the AI sees the new file immediately
        get_knowledge_index(rebuild=True)
        
        return True, "Document added and Knowledge Base rebuilt successfully!"

    except Exception as e:
        return False, f"Error adding document: {str(e)}"
    
# ... existing imports ...

def list_documents():
    """
    Returns a dataframe of files currently in the Knowledge Base.
    """
    import pandas as pd
    import os
    from datetime import datetime
    
    if not os.path.exists(Config.DOCS_DIR):
        return pd.DataFrame(columns=["File Name", "Size (KB)", "Last Modified"])
    
    files = []
    for f in os.listdir(Config.DOCS_DIR):
        path = os.path.join(Config.DOCS_DIR, f)
        if os.path.isfile(path):
            stats = os.stat(path)
            files.append({
                "File Name": f,
                "Size (KB)": round(stats.st_size / 1024, 2),
                "Last Modified": datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
            })
            
    return pd.DataFrame(files)