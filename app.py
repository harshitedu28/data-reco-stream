import streamlit as st
import pandas as pd
import sqlite3
import os

# -------------------------------------------------
# APP CONFIG
# -------------------------------------------------
st.set_page_config(page_title="🧩 Smart Reconciliation Platform", layout="wide")
st.markdown("<h1 style='text-align:center;'>🧮 Smart Reconciliation Platform</h1>", unsafe_allow_html=True)

DB_DIR = "databases"
os.makedirs(DB_DIR, exist_ok=True)

# -------------------------------------------------
# UTILITY FUNCTIONS
# -------------------------------------------------
def list_databases():
    """List all available SQLite DBs"""
    return [f for f in os.listdir(DB_DIR) if f.endswith(".db")]

def create_database(db_name):
    """Create new DB file"""
    db_path = os.path.join(DB_DIR, f"{db_name}.db")
    conn = sqlite3.connect(db_path)
    conn.close()
    return db_path

def connect_db(db_name):
    """Connect to DB"""
    db_path = os.path.join(DB_DIR, db_name)
    return sqlite3.connect(db_path)

# -------------------------------------------------
# SIDEBAR NAVIGATION
# -------------------------------------------------
st.sidebar.title("📋 Navigation Menu")

module = st.sidebar.radio(
    "Select Module",
    ["🏠 Dashboard", "📂 Data Source", "🗄 Database", "🔗 Mapping"],
    index=1
)

# -------------------------------------------------
# 🏠 DASHBOARD
# -------------------------------------------------
if module == "🏠 Dashboard":
    st.subheader("📊 Dashboard Overview (Coming Soon)")
    st.info("This will display reconciliation summaries and stats later.")

# -------------------------------------------------
# 📂 DATA SOURCE MODULE
# -------------------------------------------------
elif module == "📂 Data Source":
    st.subheader("📂 Data Source Module")
    st.write("Upload data from Excel/CSV/JSON and import into a database.")

    # Step 1: Select data source type
    st.markdown("### 1️⃣ Select Data Source Type")
    data_source = st.selectbox(
        "Choose Data Type",
        ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)"]
    )

    # Step 2: Choose target database
    st.markdown("### 2️⃣ Select Target Database")
    available_dbs = list_databases()

    if not available_dbs:
        st.warning("⚠️ No database available.")
        create_db_choice = st.radio("Database not available. Do you want to create a Database?", ["Yes", "No"])

        if create_db_choice == "Yes":
            st.session_state["redirect_to_db"] = True
            st.info("Redirecting you to Database Module…")
            st.stop()
        else:
            st.stop()
    else:
        selected_db = st.selectbox("Select Existing Database", available_dbs)

    # Step 3: Upload Files
    st.markdown("### 3️⃣ Upload Data Files")
    c1, c2 = st.columns(2)
    with c1:
        uploaded_file1 = st.file_uploader("Upload Source A", type=["xlsx", "csv", "json"])
    with c2:
        uploaded_file2 = st.file_uploader("Upload Source B", type=["xlsx", "csv", "json"])

    # Step 4: Import Button — Controlled Import
    st.markdown("### 4️⃣ Import Data")
    import_clicked = st.button("📥 Import File(s)")

    if import_clicked:
        if not uploaded_file1 and not uploaded_file2:
            st.warning("⚠️ Please upload at least one file before importing.")
            st.stop()

        # Function to import file based on type
        def import_file(file, source_name):
            if file is None:
                return None
            if data_source == "Excel (.xlsx)":
                df = pd.read_excel(file)
            elif data_source == "CSV (.csv)":
                df = pd.read_csv(file)
            else:
                df = pd.read_json(file)
            st.success(f"✅ {source_name} imported successfully!")
            st.write(f"### 🔍 Preview {source_name}")
            st.dataframe(df.head(), use_container_width=True)
            return df

        df1 = import_file(uploaded_file1, "Source A")
        df2 = import_file(uploaded_file2, "Source B")

        # Step 5: Save data into DB
        st.markdown("### 5️⃣ Save Imported Data to Database")
        conn = connect_db(selected_db)

        if df1 is not None:
            table_a = st.text_input("Enter table name for Source A", "source_a")
            if st.button("💾 Save Source A to DB"):
                df1.to_sql(table_a, conn, if_exists="replace", index=False)
                st.success(f"✅ '{table_a}' table saved successfully in '{selected_db}'")

        if df2 is not None:
            table_b = st.text_input("Enter table name for Source B", "source_b")
            if st.button("💾 Save Source B to DB"):
                df2.to_sql(table_b, conn, if_exists="replace", index=False)
                st.success(f"✅ '{table_b}' table saved successfully in '{selected_db}'")

        conn.close()

# -------------------------------------------------
# 🗄 DATABASE MODULE
# -------------------------------------------------
elif module == "🗄 Database":
    st.subheader("🗄 Database Management Module")
    st.write("Create or manage multiple databases for storing imported data.")

    existing_dbs = list_databases()
    if existing_dbs:
        st.markdown("### 📋 Existing Databases")
        st.table(pd.DataFrame({"Database Name": existing_dbs}))
    else:
        st.info("No database available yet.")

    st.markdown("---")
    st.markdown("### ➕ Create New Database")

    new_db_name = st.text_input("Enter new database name (without extension)")
    if st.button("Create Database"):
        if new_db_name.strip():
            db_path = create_database(new_db_name)
            st.success(f"✅ Database '{new_db_name}.db' created successfully at {db_path}")
        else:
            st.warning("Please enter a valid database name.")

# -------------------------------------------------
# 🔗 MAPPING MODULE
# -------------------------------------------------
elif module == "🔗 Mapping":
    st.subheader("🔗 Mapping Module")
    st.write("Visually map fields between Source A and Source B.")

    available_dbs = list_databases()
    if not available_dbs:
        st.warning("⚠️ No database found. Please create one in the Database Module.")
    else:
        selected_db = st.selectbox("Select Database", available_dbs)
        conn = connect_db(selected_db)
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)["name"].tolist()

        if len(tables) < 2:
            st.warning("You need at least two tables to create a mapping.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                table_a = st.selectbox("Select Source A Table", tables)
                df_a = pd.read_sql_query(f"SELECT * FROM {table_a} LIMIT 10", conn)
                st.dataframe(df_a.head(), use_container_width=True)
            with col2:
                table_b = st.selectbox("Select Source B Table", tables)
                df_b = pd.read_sql_query(f"SELECT * FROM {table_b} LIMIT 10", conn)
                st.dataframe(df_b.head(), use_container_width=True)

            conn.close()

            st.markdown("### ⚙️ Field Mapping")
            mapping = {}
            for col in df_a.columns:
                mapped = st.selectbox(f"{col} →", ["-- None --"] + list(df_b.columns), key=f"map_{col}")
                if mapped != "-- None --":
                    mapping[col] = mapped

            st.json(mapping)
            st.success("✅ Mapping ready (visual arrow UI coming next).")
