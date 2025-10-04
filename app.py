import streamlit as st
import pandas as pd

st.title("🧮 Data Reconciliation Tool (Full Debug & Match)")

def safe_read_csv(uploaded_file):
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
    st.error("Failed to read CSV file with supported encodings and skipping bad lines.")
    return None

uploaded_file1 = st.file_uploader("📂 Upload File 1 (CSV/Excel)", type=["csv", "xlsx"])
uploaded_file2 = st.file_uploader("📂 Upload File 2 (CSV/Excel)", type=["csv", "xlsx"])

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
        # Column names cleaning for both files
        df1.rename(columns=lambda x: x.strip(), inplace=True)
        df2.rename(columns=lambda x: x.strip(), inplace=True)

        st.write("### **Choose matching columns (one from each file):**")
        col1 = st.selectbox("File 1 column", df1.columns)
        col2 = st.selectbox("File 2 column", df2.columns)

        if st.button("Run Reconciliation"):
            # Super-strict cleaning: remove all spaces/tabs/newlines inside as well
            df1['_match_key'] = (
                df1[col1].astype(str)
                .str.replace('\s+', '', regex=True)
                .str.strip()
                .str.lower()
            )
            df2['_match_key'] = (
                df2[col2].astype(str)
                .str.replace('\s+', '', regex=True)
                .str.strip()
                .str.lower()
            )

            # Debug: display sample key values and their lengths
            st.write("File 1 sample keys:", [(v, len(v)) for v in df1['_match_key'].head(10)])
            st.write("File 2 sample keys:", [(v, len(v)) for v in df2['_match_key'].head(10)])

            # Actual reconciliation using LEFT JOIN
            merged = df1.merge(
                df2,
                how='left',
                left_on='_match_key',
                right_on='_match_key',
                suffixes=('_file1', '_file2'),
                indicator=True
            )

            st.write(f"✅ Matched: {(merged['_merge']=='both').sum()} "
                     f"❌ Unmatched: {(merged['_merge']=='left_only').sum()}  "
                     f"**Total:** {len(merged)}")

            merged['Status'] = merged['_merge'].replace({'both':'Matched', 'left_only':'Unmatched', 'right_only':'Unknown'})
            st.write("### Reconciliation Result Table")
            st.dataframe(merged.drop(columns=['_match_key', '_merge']), use_container_width=True)

            csv_result = merged.to_csv(index=False)
            st.download_button("⬇ Download Result (CSV)", csv_result, file_name="Reconciliation_Result.csv")
else:
    st.info("Upload both files to begin.")
