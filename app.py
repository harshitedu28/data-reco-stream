import streamlit as st
import pandas as pd

st.title("🧮 Data Reconciliation Tool (Multi-Condition Comparison)")

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


# ------------------------
# File Upload
# ------------------------

uploaded_file1 = st.file_uploader("📂 Upload File 1 (CSV/Excel)", type=["csv", "xlsx"])
uploaded_file2 = st.file_uploader("📂 Upload File 2 (CSV/Excel)", type=["csv", "xlsx"])

# ------------------------
# Main Logic
# ------------------------

if uploaded_file1 and uploaded_file2:
    # Read File 1
    if uploaded_file1.name.endswith('xlsx'):
        df1 = pd.read_excel(uploaded_file1)
    else:
        df1 = safe_read_csv(uploaded_file1)

    # Read File 2
    if uploaded_file2.name.endswith('xlsx'):
        df2 = pd.read_excel(uploaded_file2)
    else:
        df2 = safe_read_csv(uploaded_file2)

    # Proceed if both are valid
    if df1 is not None and df2 is not None:
        df1.rename(columns=lambda x: x.strip(), inplace=True)
        df2.rename(columns=lambda x: x.strip(), inplace=True)

        col1 = st.selectbox("📑 Select column from File 1", df1.columns)
        col2 = st.selectbox("📑 Select column from File 2", df2.columns)

        condition = st.selectbox(
            "🔍 Select Comparison Type",
            ["Equal To (=)", "Not Equal To (≠)", "Greater Than (>)", "Less Than (<)", "Greater Than or Equal (≥)", "Less Than or Equal (≤)"]
        )

        if st.button("▶ Run Reconciliation"):
            df1['_match_key'] = df1[col1].apply(clean_numeric)
            df2['_match_key'] = df2[col2].apply(clean_numeric)

            # Create all combinations for matching
            df1['_match_val'] = df1['_match_key'].apply(try_float)
            df2['_match_val'] = df2['_match_key'].apply(try_float)

            st.write("**🔹 File 1 sample keys:**", df1['_match_key'].head(5).tolist())
            st.write("**🔹 File 2 sample keys:**", df2['_match_key'].head(5).tolist())

            matched_rows = []
            condition_symbol = condition.split('(')[1][0]

            # Merge logic based on condition
            for _, row1 in df1.iterrows():
                val1 = row1['_match_val']
                match_found = False

                for _, row2 in df2.iterrows():
                    val2 = row2['_match_val']

                    try:
                        if condition_symbol == '=' and val1 == val2:
                            match_found = True
                        elif condition_symbol == '≠' and val1 != val2:
                            match_found = True
                        elif condition_symbol == '>' and float(val1) > float(val2):
                            match_found = True
                        elif condition_symbol == '<' and float(val1) < float(val2):
                            match_found = True
                        elif condition_symbol == '≥' and float(val1) >= float(val2):
                            match_found = True
                        elif condition_symbol == '≤' and float(val1) <= float(val2):
                            match_found = True
                    except Exception:
                        continue

                    if match_found:
                        matched_rows.append({**row1.to_dict(), **{f"{col2}_match": val2}, "Status": "Matched"})
                        break

                if not match_found:
                    matched_rows.append({**row1.to_dict(), **{f"{col2}_match": None}, "Status": "Unmatched"})

            result_df = pd.DataFrame(matched_rows)

            matched_count = (result_df["Status"] == "Matched").sum()
            unmatched_count = (result_df["Status"] == "Unmatched").sum()

            st.success(f"✅ Matched: {matched_count} | ❌ Unmatched: {unmatched_count} | **Total:** {len(result_df)}")
            st.write("### 📊 Reconciliation Result")
            st.dataframe(result_df, use_container_width=True)

            csv_result = result_df.to_csv(index=False)
            st.download_button("⬇ Download Result (CSV)", csv_result, file_name="Reconciliation_Result.csv")

else:
    st.info("📥 Please upload both files to begin reconciliation.")
