import streamlit as st
import pandas as pd
import sqlite3
import os
import shutil
import hashlib

# ---------------------------------------------
# CONFIG
# ---------------------------------------------
st.set_page_config(page_title="🧩 Smart Reconciliation Platform", layout="wide")
st.markdown("<h1 style='text-align:center;'>🧮 Smart Reconciliation Platform</h1>", unsafe_allow_html=True)

DB_DIR = "databases"
os.makedirs(DB_DIR, exist_ok=True)

SECURITY_DB = os.path.join(DB_DIR, "security.db")

# ---------------------------------------------
# SECURITY SETUP
# ---------------------------------------------
def init_security_db():
    conn = sqlite3.connect(SECURITY_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    conn = sqlite3.connect(SECURITY_DB)
    conn.execute("INSERT OR REPLACE INTO users (username, password_hash) VALUES (?, ?)", 
                 (username, hash_password(password)))
    conn.commit()
    conn.close()

def validate_user(username, password):
    conn = sqlite3.connect(SECURITY_DB)
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return row and row[0] == hash_password(password)

init_security_db()

# ---------------------------------------------
# DATABASE HELPERS
# ---------------------------------------------
def list_databases():
    return [f for f in os.listdir(DB_DIR) if f.endswith(".db") and f != "security.db"]

def create_database(db_name):
    path = os.path.join(DB_DIR, f"{db_name}.db")
    conn = sqlite3.connect(path)
    conn.close()
    folder = os.path.join(DB_DIR, f"{db_name}_files")
    os.makedirs(folder, exist_ok=True)
    return path

def connect_db(db_name):
    return sqlite3.connect(os.path.join(DB_DIR, db_name))

def get_tables(db_name):
    conn = connect_db(db_name)
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(query, conn)
    conn.close()
    return tables["name"].tolist()

# ---------------------------------------------
# SESSION STATE
# ---------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "current_module" not in st.session_state:
    st.session_state.current_module = "📂 Data Source"

# ---------------------------------------------
# LOGIN PAGE
# ---------------------------------------------
def login_page():
    st.markdown("<h3 style='text-align:center;'>🔐 Login to Continue</h3>", unsafe_allow_html=True)
    username = st.text_input("👤 Username")
    password = st.text_input("🔑 Password", type="password")

    if st.button("Login"):
        if validate_user(username, password):
            st.session_state.authenticated = True
            st.session_state.current_user = username
            st.success(f"✅ Welcome, {username}!")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

# ---------------------------------------------
# LOGOUT
# ---------------------------------------------
def logout_button():
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()

# ---------------------------------------------
# MAIN APP (AFTER LOGIN)
# ---------------------------------------------
if not st.session_state.authenticated:
    login_page()

else:
    logout_button()

    st.sidebar.title("📋 Navigation Menu")
    module = st.sidebar.radio(
        "Select Module",
        ["🏠 Dashboard", "📂 Data Source", "🗄 Database", "🔗 Mapping", "🔒 Security"],
        index=["🏠 Dashboard", "📂 Data Source", "🗄 Database", "🔗 Mapping", "🔒 Security"].index(st.session_state.current_module)
    )

    st.session_state.current_module = module

    # -------------------------------------------------
    # 📂 DATA SOURCE MODULE
    # -------------------------------------------------
    if module == "📂 Data Source":
        st.subheader("📂 Data Source Module")
        st.write("Upload your file and import data into a selected database.")

        # Step 1: File Type
        st.markdown("### 1️⃣ Select Data Source Type")
        file_type = st.selectbox("Choose File Type", ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)"])

        # Step 2: Upload File
        st.markdown("### 2️⃣ Upload File to Import")
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

        # Step 3: Select or Create Database
        st.markdown("### 3️⃣ Select Target Database")
        available_dbs = list_databases()
        db_display_list = ["~ None ~"] if not available_dbs else available_dbs
        selected_db = st.selectbox("Choose Database", db_display_list)

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

        create_new_db = st.button("➕ Create New Database")
        if create_new_db:
            st.session_state.current_module = "🗄 Database"
            st.rerun()

        if selected_db == "~ None ~":
            st.warning("⚠️ No database available. Please create one before importing.")
            st.stop()

        # Step 4: Import Data
        st.markdown("### 4️⃣ Import Data into Database")
        table_name = st.text_input("Enter Table Name", "imported_data")

        if st.button("📥 Import Data"):
            if uploaded_file is None:
                st.warning("⚠️ Please upload a file first.")
                st.stop()

            conn = connect_db(selected_db)
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            conn.close()

            db_base = selected_db.replace(".db", "")
            db_folder = os.path.join(DB_DIR, f"{db_base}_files")
            os.makedirs(db_folder, exist_ok=True)
            dest = os.path.join(db_folder, uploaded_file.name)
            with open(dest, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success(f"✅ Data imported successfully into '{selected_db}' (Table: {table_name})")
            st.session_state["last_imported_db"] = selected_db
            st.session_state["last_imported_table"] = table_name

    # -------------------------------------------------
    # 🗄 DATABASE MODULE
    # -------------------------------------------------
    elif module == "🗄 Database":
        st.subheader("🗄 Database Management Module")
        existing = list_databases()

        if not existing:
            st.info("No database created yet.")
        else:
            selected_view_db = st.selectbox("Select Database to View", existing)
            tables = get_tables(selected_view_db)

            if not tables:
                st.warning("⚠️ No tables found in this database.")
            else:
                st.markdown(f"### 📊 Tables in **{selected_view_db}**")
                for t in tables:
                    with st.expander(f"📁 {t}"):
                        conn = connect_db(selected_view_db)
                        preview = pd.read_sql_query(f"SELECT * FROM {t} LIMIT 10", conn)
                        conn.close()
                        st.dataframe(preview, use_container_width=True)

        # Create DB
        st.markdown("---")
        st.markdown("### ➕ Create New Database")
        new_db_name = st.text_input("Enter New Database Name (without .db)")
        if st.button("Create Database"):
            if new_db_name.strip():
                path = create_database(new_db_name)
                st.success(f"✅ Database '{new_db_name}.db' created successfully at {path}")
                st.rerun()
            else:
                st.warning("Please enter a valid name.")

    # -------------------------------------------------
    # 🔒 SECURITY MODULE
    # -------------------------------------------------
    elif module == "🔒 Security":
        st.subheader("🔒 Security Management")
        st.write("Create and manage user credentials.")

        st.markdown("### ➕ Create New User")
        new_user = st.text_input("Enter New Username")
        new_pass = st.text_input("Enter Password", type="password")

        if st.button("Add User"):
            if new_user.strip() and new_pass.strip():
                add_user(new_user, new_pass)
                st.success(f"✅ User '{new_user}' created successfully!")
            else:
                st.warning("Please enter valid username and password.")

        # View users
        conn = sqlite3.connect(SECURITY_DB)
        users = pd.read_sql_query("SELECT username FROM users", conn)
        conn.close()

        if not users.empty:
            st.markdown("### 👥 Registered Users")
            st.table(users)
        else:
            st.info("No users registered yet.")
