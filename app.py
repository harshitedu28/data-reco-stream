import streamlit as st
import pandas as pd

st.set_page_config(page_title="Smart Reconciliation Tool", layout="wide")

# Sidebar navigation
st.sidebar.header("📋 Navigation Menu")
selected_module = st.sidebar.radio(
    "Select Module", 
    ["📂 Data Load Module", "🧩 Design Module"]
)

# Placeholder for uploaded data
if "df1" not in st.session_state:
    st.session_state.df1 = None
if "df2" not in st.session_state:
    st.session_state.df2 = None

# ===============================
# 📂 DATA LOAD MODULE - Main Area
# ===============================
if selected_module == "📂 Data Load Module":
    st.title("📂 Data Load Module")
    st.markdown("Select file type and upload both source files.")

    col1, col2 = st.columns(2)

    with col1:
        file_type = st.selectbox("Select File Type", ["CSV", "XLSX"], key="file_type")

    st.markdown("---")
    st.subheader("Upload Your Files")

    c1, c2 = st.columns(2)
    with c1:
        uploaded_file1 = st.file_uploader("Upload Source A (File 1)", type=[file_type.lower()])
    with c2:
        uploaded_file2 = st.file_uploader("Upload Source B (File 2)", type=[file_type.lower()])

    if uploaded_file1 and uploaded_file2:
        if file_type == "CSV":
            df1 = pd.read_csv(uploaded_file1)
            df2 = pd.read_csv(uploaded_file2)
        else:
            df1 = pd.read_excel(uploaded_file1)
            df2 = pd.read_excel(uploaded_file2)

        st.session_state.df1 = df1
        st.session_state.df2 = df2

        st.success("✅ Files uploaded successfully!")
        st.markdown("### 🧠 Detected Columns")
        st.write(f"**File 1 Columns:** {list(df1.columns)}")
        st.write(f"**File 2 Columns:** {list(df2.columns)}")

        st.markdown("---")
        st.info("Next Step: Go to 🧩 Design Module to create mappings & compare data.")

# ===============================
# 🧩 DESIGN MODULE - Main Area
# ===============================
elif selected_module == "🧩 Design Module":
    st.title("🧩 Design & Mapping Module")

    if st.session_state.df1 is None or st.session_state.df2 is None:
        st.warning("⚠ Please upload data first using the Data Load Module.")
    else:
        df1 = st.session_state.df1
        df2 = st.session_state.df2

        st.markdown("### Step 1: Column Mapping")
        st.write("Match the columns from both datasets below:")
        mapping = {}
        for col in df1.columns:
            mapped = st.selectbox(f"{col} →", ["-- None --"] + list(df2.columns), key=f"map_{col}")
            if mapped != "-- None --":
                mapping[col] = mapped

        st.json(mapping)

        st.markdown("### Step 2: Define Condition / Prompt")
        prompt = st.text_area("Describe your expectation (e.g., 'Amount should match')")
        st.info("This will be used later to determine comparison logic automatically.")
