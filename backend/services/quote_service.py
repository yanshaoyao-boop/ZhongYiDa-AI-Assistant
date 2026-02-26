import pandas as pd
import os
from typing import Dict, Any, List

# In-memory storage for parsed quotes
# In production, we might store this in a relational DB or just load it on startup
QUOTES_CACHE: Dict[str, pd.DataFrame] = {}
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "quotes")

def init_quote_directory():
    os.makedirs(DATA_DIR, exist_ok=True)

def parse_quote_file(file_path: str) -> pd.DataFrame:
    """Parse an Excel or CSV quote file into a pandas DataFrame."""
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        elif ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported quote format: {ext}")
            
        # Basic cleaning: drop fully empty rows/columns
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        # Convert all NaNs to empty strings for easier JSON serialization later
        df = df.fillna("")
        return df
    except Exception as e:
        print(f"Error parsing quote file {file_path}: {e}")
        return pd.DataFrame()

def load_all_quotes():
    """Load all quote files from the data directory into cache."""
    init_quote_directory()
    QUOTES_CACHE.clear()
    
    for filename in os.listdir(DATA_DIR):
        file_path = os.path.join(DATA_DIR, filename)
        if os.path.isfile(file_path):
            df = parse_quote_file(file_path)
            if not df.empty:
                QUOTES_CACHE[filename] = df
    return list(QUOTES_CACHE.keys())

def get_quote_data_as_string(filename: str = None) -> str:
    """Return quote data as formatted text for the LLM to read."""
    if not QUOTES_CACHE:
        load_all_quotes()
        
    result = ""
    if filename and filename in QUOTES_CACHE:
        df = QUOTES_CACHE[filename]
        result += f"--- 报价表: {filename} ---\n"
        # Convert DataFrame to Markdown table for easier reading by LLM
        result += df.to_markdown(index=False)
        result += "\n\n"
    else:
        for name, df in QUOTES_CACHE.items():
            result += f"--- 报价表: {name} ---\n"
            # Get max 50 rows per table to avoid token overflow
            sample_df = df.head(50)
            result += sample_df.to_markdown(index=False)
            if len(df) > 50:
                result += f"\n*... (还有 {len(df) - 50} 行数据未展示) ...*\n"
            result += "\n\n"
            
    return result

# Initialize on module import
init_quote_directory()
try:
    load_all_quotes()
except Exception:
    pass
