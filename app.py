import streamlit as st
import pandas as pd
import sqlite3
import os

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(page_title="🧩 Smart Reconciliation Platform", layout="wide")
st.markdown("<h1 style='text-align:center;'>🧮 Smart Reconciliation Platform</h1>", unsafe_allow_html=True)

DB_DIR = "databases"
os.makedirs(DB_DIR, exist_ok=True)

# -------------------------------------------------
# FUNCTIONS
# -------------------------------------------------
def list_databases():
    return [f for f in os.listdir(DB_DIR) if f.endswith(".db")]

def create_database(db_name):
    path = os.path.join(DB_DIR, f"{db_name}.db")
    conn = sqlite3.connect(path)
    conn.close()
    return path

def connect_db(db_name):
    return sqlite3.connect(os.path.join(DB_DIR, db_name))

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.title("📋 Navigation Menu")

module = st.sidebar.radio(
    "Select Module",
    ["🏠 Dashboard", "📂 Data Source", "🗄 Database", "🔗 Mapping"],
    index=1
)

# -------------------------------------------------
# DATA SOURCE MODULE
# -------------------------------------------------
if module == "📂 Data Source":
    st.subheader("📂 Data Source Module")
    st.write("Upload single data file and import it into a selected database.")

    # Step 1: Choose file type
    st.markdown("### 1️⃣ Select Data Source Type")
    file_type = st.selectbox("Choose File Type", ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)"])

    # Step 2: Upload single file
    st.markdown("### 2️⃣ Upload Source File")
    uploaded_file = st.file_uploader("Upload Data File", type=["xlsx", "csv", "json"])

    df = None
    if uploaded_file:
        if file_type == "Excel (.xlsx)":
            df = pd.read_excel(uploaded_file)
        elif file_type == "CSV (.csv)":
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_json(uploaded_file)

        st.success("✅ File uploaded successfully!")
        st.dataframe(df.head(), use_container_width=True)

    # Step 3: Select Database (Dropdown + Create Option)
    st.markdown("### 3️⃣ Select Target Database")
    available_dbs = list_databases()

    if available_dbs:
        selected_db = st.selectbox("Choose Existing Database", available_dbs)
        st.info(f"Selected Database: {selected_db}")
    else:
        st.warning("⚠️ No database found.")
        create_option = st.radio("Do you want to create a new Database?", ["Yes", "No"], key="create_db_radio")
        if create_option == "Yes":
            st.info("Redirecting you to Database Module…")
            st.session_state["redirect_to_db"] = True
            st.stop()
        else:
            st.stop()

    # Step 4: Import Data
    st.markdown("### 4️⃣ Import Data to Database")

    if st.button("📥 Import Data"):
        if uploaded_file is None:
            st.warning("⚠️ Please upload a file first.")
            st.stop()

        conn = connect_db(selected_db)
        table_name = st.text_input("Enter Table Name", "imported_data")

        if not table_name.strip():
            st.warning("Please enter a valid table name.")
        else:
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            st.success(f"✅ Data imported successfully into '{selected_db}' as table '{table_name}'")
        conn.close()

# -------------------------------------------------
# DATABASE MODULE
# -------------------------------------------------
elif module == "🗄 Database":
    st.subheader("🗄 Database Management Module")

    existing = list_databases()
    if existing:
        st.markdown("### 📋 Existing Databases")
        st.table(pd.DataFrame({"Database": existing}))
    else:
        st.info("No databases created yet.")

    st.markdown("---")
    new_db_name = st.text_input("Enter New Database Name (without .db)")
    if st.button("Create Database"):
        if new_db_name.strip():
            path = create_database(new_db_name)
            st.success(f"✅ Database '{new_db_name}.db' created successfully at {path}")
        else:
            st.warning("Please enter a valid name.")

# -------------------------------------------------
# OTHER MODULES
# -------------------------------------------------
elif module == "🏠 Dashboard":
    st.subheader("📊 Dashboard (Coming Soon)")

elif module == "🔗 Mapping":
    st.subheader("🔗 Mapping Module (Under Design)")
