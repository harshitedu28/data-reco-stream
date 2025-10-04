import streamlit as st
import pandas as pd

st.title("🧮 Data Reconciliation Tool (Free Streamlit Version)")

def safe_read_csv(uploaded_file):
    for encoding in ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252', 'unicode_escape']:
        try:
            uploaded_file.seek(0)  # Reset to start of file before reading
            return pd.read_csv(
                uploaded_file,
                encoding=encoding,
                on_bad_lines='skip',       # Skip bad/malformed lines
                encoding_errors='ignore'    # Ignore encoding errors
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
        st.write("### **Choose columns to match (can pick multiple)**")
        col1 = st.multiselect("File 1 columns", df1.columns)
        col2 = st.multiselect("File 2 columns", df2.columns)

        if col1 and col2:
            if len(col1) != len(col2):
                st.error("Number of columns selected for both files must be same!")
            else:
                if st.button("Run Reconciliation"):
                    with st.spinner("Reconciling..."):
                        key1 = df1[col1].astype(str).agg('|'.join, axis=1).str.lower()
                        key2 = df2[col2].astype(str).agg('|'.join, axis=1).str.lower()
                        df2_map = pd.Series(df2.index, index=key2)
                        matches, mismatched = [], []

                        for i, k in enumerate(key1):
                            idx = df2_map.get(k, None)
                            if pd.notnull(idx):
                                matches.append((i, int(idx)))
                            else:
                                mismatched.append(i)

                        summary = f"✅ Matched: {len(matches)} &nbsp; ❌ Unmatched: {len(mismatched)} &nbsp; **Total:** {len(matches)+len(mismatched)}"
                        st.markdown(f"<div style='background:#FFF;padding:10px;border-radius:6px;'>{summary}</div>", unsafe_allow_html=True)

                        result_table = pd.DataFrame({
                            'Status': ['Matched']*len(matches) + ['Unmatched']*len(mismatched),
                            'File1 Record': [df1.iloc[i].to_dict() for i,_ in matches] + [df1.iloc[i].to_dict() for i in mismatched],
                            'File2 Record': [df2.iloc[j].to_dict() for _,j in matches] + ['No Match']*len(mismatched)
                        })

                        style = result_table.style.apply(
                            lambda row: ['background-color: #d4edda' if row.Status=="Matched" else 'background-color: #f8d7da']*len(row), axis=1
                        )
                        st.write("### Result Table")
                        st.dataframe(style, use_container_width=True)

                        csv_result = result_table.to_csv(index=False)
                        st.download_button("⬇ Download Result (CSV)", csv_result, file_name="Reconciliation_Result.csv")

        else:
            st.info("Please select columns to match from both files.")
else:
    st.info("Upload both files to begin.")
