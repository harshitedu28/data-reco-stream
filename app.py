import streamlit as st
import pandas as pd
import re

st.title("🧮 Smart Data Reconciliation Tool (Prompt + Multi-Condition)")

# ------------------------
# Helper Functions
# ------------------------

def safe_read_csv(uploaded_file):
    """Safely read CSV with multiple encoding fallbacks."""
    for encoding in ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252', 'unicode_escape']:
        try:
            uploaded_file.seek(0)
            return pd.read_csv(
                uploaded_file,
                encoding=encoding,
                on_bad_lines='skip',
                encoding_errors='ignore'
            )
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
    """Infer comparison condition from user prompt."""
    prompt_text = prompt_text.lower()

    # Detect type of comparison based on common keywords
    if any(word in prompt_text for word in ["same", "equal", "match", "equals", "should be identical", "same value"]):
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
        return "="  # default to equal if unclear


def perform_comparison(df1, df2, col1, col2, condition):
    """Perform reconciliation based on detected condition."""
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

    result_df = pd.DataFrame(matched_rows)
    return result_df


# ------------------------
# File Upload
# ------------------------

uploaded_file1 = st.file_uploader("📂 Upload File 1 (CSV/Excel)", type=["csv", "xlsx"])
uploaded_file2 = st.file_uploader("📂 Upload File 2 (CSV/Excel)", type=["csv", "xlsx"])

if uploaded_file1 and uploaded_file2:
    # Read files
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

        col1 = st.selectbox("📑 Select column from File 1", df1.columns)
        col2 = st.selectbox("📑 Select column from File 2", df2.columns)

        st.markdown("### 🧠 Smart Prompt Mode")
        user_prompt = st.text_area(
            "Describe your expectation (e.g. 'File 1 amount should be greater than File 2 amount' or 'Invoice numbers should match')"
        )

        manual_condition = st.selectbox(
            "Or manually select comparison type (optional)",
            ["Auto (based on prompt)", "Equal To (=)", "Not Equal To (≠)", "Greater Than (>)",
             "Less Than (<)", "Greater Than or Equal (≥)", "Less Than or Equal (≤)"]
        )

        if st.button("🚀 Run Smart Reconciliation"):
            # Determine condition
            if manual_condition == "Auto (based on prompt)":
                condition = detect_condition_from_prompt(user_prompt)
                st.info(f"🧩 Auto-detected condition based on prompt: **{condition}**")
            else:
                condition = manual_condition.split('(')[1][0]

            result_df = perform_comparison(df1, df2, col1, col2, condition)

            matched_count = (result_df["Status"] == "Matched").sum()
            unmatched_count = (result_df["Status"] == "Unmatched").sum()

            st.success(f"✅ Matched: {matched_count} | ❌ Unmatched: {unmatched_count} | **Total:** {len(result_df)}")
            st.write("### 📊 Reconciliation Result")
            st.dataframe(result_df, use_container_width=True)

            csv_result = result_df.to_csv(index=False)
            st.download_button("⬇ Download Result (CSV)", csv_result, file_name="Reconciliation_Result.csv")

else:
    st.info("📥 Please upload both files to begin reconciliation.")
