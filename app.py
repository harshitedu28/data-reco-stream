import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Smart Reconciliation Tool", layout="wide")
st.title("🧮 Smart Data Reconciliation Dashboard")

# ------------------------
# Helper Functions
# ------------------------

def safe_read_csv(uploaded_file):
    """Safely read CSV with multiple encoding fallbacks."""
    for encoding in ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252', 'unicode_escape']:
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding=encoding, on_bad_lines='skip', encoding_errors='ignore')
        except Exception:
            continue
    st.error("❌ Failed to read CSV file with supported encodings.")
    return None


def clean_numeric(value):
    """Clean and normalize numeric or string values for comparison."""
    if pd.isna(value):
        return None
    s = str(value).strip()
    if s.endswith('.0'):
        s = s[:-2]
    return s


def try_float(value):
    """Convert to float if possible, else return original."""
    try:
        return float(value)
    except Exception:
        return value


def detect_condition_from_prompt(prompt_text):
    """Infer comparison condition from natural language prompt."""
    prompt_text = prompt_text.lower()

    if any(word in prompt_text for word in ["same", "equal", "match", "equals", "identical"]):
        return "="
    elif any(word in prompt_text for word in ["not same", "different", "not equal", "mismatch"]):
        return "≠"
    elif any(word in prompt_text for word in ["greater", "more than", "higher", "above"]):
        return ">"
    elif any(word in prompt_text for word in ["less", "lower", "below", "smaller"]):
        return "<"
    elif any(word in prompt_text for word in ["greater or equal", "at least"]):
        return "≥"
    elif any(word in prompt_text for word in ["less or equal", "at most"]):
        return "≤"
    else:
        return "="  # Default


def perform_comparison(df1, df2, col1, col2, condition):
    """Perform reconciliation based on the detected condition."""
    df1['_match_key'] = df1[col1].apply(clean_numeric)
    df2['_match_key'] = df2[col2].apply(clean_numeric)
    df1['_val'] = df1['_match_key'].apply(try_float)
    df2['_val'] = df2['_match_key'].apply(try_float)

    matched_rows = []

    for _, row1 in df1.iterrows():
        val1 = row1['_val']
        match_found = False

        for _, row2 in df2.iterrows():
            val2 = row2['_val']
            try:
                if condition == "=" and val1 == val2:
                    match_found = True
                elif condition == "≠" and val1 != val2:
                    match_found = True
                elif condition == ">" and float(val1) > float(val2):
                    match_found = True
                elif condition == "<" and float(val1) < float(val2):
                    match_found = True
                elif condition == "≥" and float(val1) >= float(val2):
                    match_found = True
                elif condition == "≤" and float(val1) <= float(val2):
                    match_found = True
            except Exception:
                continue

            if match_found:
                matched_rows.append({**row1.to_dict(), **{f"{col2}_match": val2}, "Status": "Matched"})
                break

        if not match_found:
            matched_rows.append({**row1.to_dict(), **{f"{col2}_match": None}, "Status": "Unmatched"})

    return pd.DataFrame(matched_rows)


def save_mapping(mapping_name, mapping_dict):
    """Save mapping as JSON."""
    os.makedirs("config", exist_ok=True)
    with open(f"config/{mapping_name}.json", "w", encoding="utf-8") as f:
        json.dump(mapping_dict, f, indent=4)
    st.success(f"✅ Mapping saved as config/{mapping_name}.json")


def load_saved_mappings():
    """List saved mapping files."""
    os.makedirs("config", exist_ok=True)
    return [f.replace(".json", "") for f in os.listdir("config") if f.endswith(".json")]


def load_mapping_file(mapping_name):
    """Load mapping JSON."""
    with open(f"config/{mapping_name}.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------
# Sidebar Layout with Modules
# ------------------------

st.sidebar.header("📋 Navigation Menu")

# --- Data Load Module ---
with st.sidebar.expander("📂 Data Load Module", expanded=True):
    st.write("Upload Source Files")
    uploaded_file1 = st.file_uploader("Upload Source A (File 1)", type=["csv", "xlsx"], key="file1")
    uploaded_file2 = st.file_uploader("Upload Source B (File 2)", type=["csv", "xlsx"], key="file2")

# --- Design Module ---
with st.sidebar.expander("🧩 Design Module", expanded=False):
    st.write("Create or Load Column Mapping Configuration")
    mapping_mode = st.radio("Choose Mapping Option", ["Create New Mapping", "Load Saved Mapping"], key="map_mode")
    mapping_name_input = st.text_input("Mapping name (for saving/loading):", key="map_name")


# ------------------------
# Main Page (Right Side)
# ------------------------

if uploaded_file1 and uploaded_file2:
    i
