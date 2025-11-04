import streamlit as st
import pandas as pd
import json
import os

st.title("🧮 Smart Data Reconciliation Tool (Mapping + Prompt + Multi-Condition)")

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


# ------------------------
# Mapping Interface Logic
# ------------------------

def save_mapping(mapping_name, mapping_dict):
    """Save mapping as JSON in config folder."""
    os.makedirs("config", exist_ok=True)
    with open(f"config/{mapping_name}.json", "w", encoding="utf-8") as f:
        json.dump(mapping_dict, f, indent=4)
    st.success(f"✅ Mapping saved as config/{mapping_name}.json")


def load_saved_mappings():
    """Return a list of saved mapping files."""
    os.makedirs("config", exist_ok=True)
    return [f.replace(".json", "") for f in os.listdir("config") if f.endswith(".json")]


def load_mapping_file(mapping_name):
    """Load a saved mapping JSON."""
    with open(f"config/{mapping_name}.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------
# File Upload Section
# ------------------------

uploaded_file1 = st.file_uploader("📂 Upload Source A (File 1)", type=["csv", "xlsx"])
uploaded_file2 = st.file_uploader("📂 Upload Source B (File 2)", type=["csv", "xlsx"])

if uploaded_file1 and uploaded_file2:
    if uploaded_file1.name.endswith('xlsx'):
        df1 = pd.read_excel(uploaded_file1)
    else:
        df1 = safe_read_csv(uploaded_file1)

    if uploaded_file2.name.endswith('xlsx'):
        df2 = pd.read_excel(uploaded_file2)
    else:
        df2 = safe_read_csv(uploaded_file2)

    if df1 is not None and df2 is not None:
        df1.rename(columns=lambda x: x.strip(), inplace=True)
        df2.rename(columns=lambda x: x.strip(), inplace=True)

        st.subheader("⚙️ Step 1: Column Detection")
        st.write(f"✅ Columns detected in **File 1**: {list(df1.columns)}")
        st.write(f"✅ Columns detected in **File 2**: {list(df2.columns)}")

        # Step 4: Load or Create Mapping
        st.subheader("🧩 Step 2: Column Mapping Interface")
        mapping_mode = st.radio("Choose Mapping Option", ["Create New Mapping", "Load Saved Mapping"])

        mapping_dict = {}

        if mapping_mode == "Create New Mapping":
            st.write("Map columns from File 1 → File 2:")
            for col in df1.columns:
                mapped_col = st.selectbox(f"File 1: {col}", ["-- None --"] + list(df2.columns), key=col)
                if mapped_col != "-- None --":
                    mapping_dict[col] = mapped_col

            mapping_name = st.text_input("Enter mapping name to save (e.g., bank_mapping)")
            if st.button("💾 Save Mapping"):
                if mapping_dict and mapping_name.strip():
                    save_mapping(mapping_name.strip(), mapping_dict)
                else:
                    st.error("Please provide a mapping name and map at least one column.")

        else:
            saved_mappings = load_saved_mappings()
            if saved_mappings:
                selected_mapping = st.selectbox("Select saved mapping", saved_mappings)
                if st.button("📂 Load Mapping"):
                    mapping_dict = load_mapping_file(selected_mapping)
                    st.success(f"Loaded mapping: {mapping_dict}")
            else:
                st.warning("No saved mappings found in 'config/' folder.")

        # Proceed if mapping is ready
        if mapping_dict:
            st.subheader("🧠 Step 3: Define Comparison Logic")

            user_prompt = st.text_area(
                "Describe your reconciliation expectation (e.g. 'Amounts should match', 'File 1 value should be greater than File 2')"
            )

            manual_condition = st.selectbox(
                "Or manually select comparison type",
                ["Auto (based on prompt)", "Equal To (=)", "Not Equal To (≠)", "Greater Than (>)",
                 "Less Than (<)", "Greater Than or Equal (≥)", "Less Than or Equal (≤)"]
            )

            if st.button("🚀 Run Reconciliation"):
                if manual_condition == "Auto (based on prompt)":
                    condition = detect_condition_from_prompt(user_prompt)
                    st.info(f"🧩 Auto-detected condition: **{condition}**")
                else:
                    condition = manual_condition.split('(')[1][0]

                results = []
                for col1, col2 in mapping_dict.items():
                    st.write(f"Comparing: **{col1} ↔ {col2}** ({condition})")
                    result_df = perform_comparison(df1, df2, col1, col2, condition)
                    result_df['Field_Compared'] = f"{col1} ↔ {col2}"
                    results.append(result_df)

                final_df = pd.concat(results, ignore_index=True)
                matched_count = (final_df["Status"] == "Matched").sum()
                unmatched_count = (final_df["Status"] == "Unmatched").sum()

                st.success(f"✅ Matched: {matched_count} | ❌ Unmatched: {unmatched_count} | **Total:** {len(final_df)}")
                st.write("### 📊 Reconciliation Result")
                st.dataframe(final_df, use_container_width=True)

                csv_result = final_df.to_csv(index=False)
                st.download_button("⬇ Download Result (CSV)", csv_result, file_name="Reconciliation_Result.csv")

else:
    st.info("📥 Please upload both files to begin reconciliation.")
