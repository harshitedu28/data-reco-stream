import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="📂 Smart Data Load Module", layout="wide")

DB_PATH = "data_store.db"

# Ensure database exists
if not os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    conn.close()


# ------------------------------
# Utility Functions
# ------------------------------
def init_db():
    """Initialize SQLite connection."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def save_to_db(df, table_name):
    """Save dataframe to SQLite database."""
    conn = init_db()
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()


def get_saved_tables():
    """List saved datasets."""
    conn = init_db()
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
    conn.close()
    return tables["name"].tolist()


def preview_db_table(table_name):
    """Fetch few records for preview."""
    conn = init_db()
    df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 10;", conn)
    conn.close()
    return df


# ------------------------------
# Page UI
# ------------------------------
st.title("📂 Data Load & Storage Module")
st.markdown("""
This module lets you **import data from Excel or CSV**, 
store it securely into a **local database**, and reuse it later 
for reconciliation or mapping design.
""")

tab1, tab2 = st.tabs(["📥 Import New Data", "🗃 View Saved Data"])

# ================================================
# TAB 1: DATA IMPORT
# ================================================
with tab1:
    st.subheader("Step 1️⃣ Choose Data Source Type")

    data_source = st.radio(
        "Select Source Type",
        ["Excel File (XLSX)", "CSV File"],
        horizontal=True
    )

    st.markdown("---")
    st.subheader("Step 2️⃣ Upload Source Files")

    c1, c2 = st.columns(2)
    with c1:
        uploaded_file1 = st.file_uploader("Upload Source A", type=["xlsx", "csv"])
    with c2:
        uploaded_file2 = st.file_uploader("Upload Source B", type=["xlsx", "csv"])

    if uploaded_file1 and uploaded_file2:
        # Load file based on source type
        if data_source == "CSV File":
            df1 = pd.read_csv(uploaded_file1)
            df2 = pd.read_csv(uploaded_file2)
        else:
            df1 = pd.read_excel(uploaded_file1)
            df2 = pd.read_excel(uploaded_file2)

        st.success("✅ Data Loaded Successfully!")
        st.write("### 🔍 Preview Source A")
        st.dataframe(df1.head(), use_container_width=True)
        st.write("### 🔍 Preview Source B")
        st.dataframe(df2.head(), use_container_width=True)

        st.markdown("---")
        st.subheader("Step 3️⃣ Save Data into Local Database")

        dataset_name_a = st.text_input("Enter name for Source A dataset (table name)", "source_a")
        dataset_name_b = st.text_input("Enter name for Source B dataset (table name)", "source_b")

        if st.button("💾 Save to Database"):
            try:
                save_to_db(df1, dataset_name_a)
                save_to_db(df2, dataset_name_b)
                st.success(f"🎉 Data saved successfully to database as '{dataset_name_a}' and '{dataset_name_b}'!")
            except Exception as e:
                st.error(f"❌ Failed to save: {e}")


# ================================================
# TAB 2: SAVED DATA PREVIEW
# ================================================
with tab2:
    st.subheader("🗂 Available Saved Datasets")
    saved_tables = get_saved_tables()

    if not saved_tables:
        st.info("No saved data found yet. Upload and save data first.")
    else:
        selected_table = st.selectbox("Select dataset to preview", saved_tables)
        df_preview = preview_db_table(selected_table)
        st.dataframe(df_preview, use_container_width=True)

        st.download_button(
            label="⬇ Download Dataset (CSV)",
            data=df_preview.to_csv(index=False),
            file_name=f"{selected_table}.csv"
        )
