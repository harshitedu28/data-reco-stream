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
# 📂 DATA SOURCE MODULE
# -------------------------------------------------
if module == "📂 Data Source":
    st.subheader("📂 Data Source Module")
    st.write("Upload data file and import it into a database.")

    # Step 1: File Type
    st.markdown("### 1️⃣ Select Data Source Type")
    file_type = st.selectbox("Choose File Type", ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)"])

    # Step 2: Upload
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

    # Step 3: Database Selection
    st.markdown("### 3️⃣ Select Target Database")

    available_dbs = list_databases()
    db_display_list = ["~ None ~"] if not available_dbs else available_dbs

    selected_db = st.selectbox("Choose Database", db_display_list)

    # Create new DB button (with hover style)
    st.markdown("""
        <style>
        .create-db-btn {
            background-color: #f0f2f6;
            color: #0b5394;
            border: 1px solid #0b5394;
            border-radius: 8px;
            padding: 8px 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .create-db-btn:hover {
            background-color: #0b5394;
            color: white;
            border-color: #073763;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("Select existing database or create a new one if not available.")
    with col2:
        create_btn = st.markdown('<button class="create-db-btn" id="createDB">➕ Create New Database</button>', unsafe_allow_html=True)

    # Handle "None" case
    if selected_db == "~ None ~":
        st.warning("⚠️ No database available. Please create a new database before importing data.")
        st.stop()

    # Step 4: Import Data
    st.markdown("### 4️⃣ Import Data to Database")
    if st.button("📥 Import Data"):
        if uploaded_file is None:
            st.warning("⚠️ Please upload a file first.")
            st.stop()

        table_name = st.text_input("Enter Table Name", "imported_data")

        if not table_name.strip():
            st.warning("Please enter a valid table name.")
        else:
            conn = connect_db(selected_db)
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            conn.close()
            st.success(f"✅ Data imported successfully into '{selected_db}' as table '{table_name}'")

# -------------------------------------------------
# 🗄 DATABASE MODULE
# -------------------------------------------------
elif module == "🗄 Database":
    st.subheader("🗄 Database Management Module")

    existing = list_databases()
    if existing:
        st.markdown("### 📋 Existing Databases")
        st.table(pd.DataFrame({"Database": existing}))
    else:
        st.info("No database created yet.")

    st.markdown("---")
    new_db_name = st.text_input("Enter New Database Name (without .db)")
    if st.button("Create Database"):
        if new_db_name.strip():
            path = create_database(new_db_name)
            st.success(f"✅ Database '{new_db_name}.db' created successfully at {path}")
        else:
            st.warning("Please enter a valid name.")
