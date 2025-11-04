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
    st.info("This will show stats, logs, and mapping history later.")

# -------------------------------------------------
# 📂 DATA SOURCE MODULE
# -------------------------------------------------
elif module == "📂 Data Source":
    st.subheader("📂 Data Source Module")
    st.write("Upload data from Excel/CSV/JSON and save it to a database for reconciliation or mapping.")

    # Step 1: Select data source type
    data_source = st.selectbox(
        "Select Data Source Type",
        ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)"]
    )

    # Step 2: Check available databases
    st.markdown("### 🗄 Select Target Database")
    available_dbs = list_databases()

    if not available_dbs:
        st.warning("⚠️ No database available.")
        create_db_choice = st.radio("Database not available. Do you want to create a Database?", ["Yes", "No"])

        if create_db_choice == "Yes":
            st.session_state["redirect_to_db"] = True
            st.info("Redirecting you to Database Module...")
        else:
            st.stop()
    else:
        selected_db = st.selectbox("Select Database", available_dbs)

        # Step 3: Upload files
        st.markdown("### 📥 Upload Source Files")
        c1, c2 = st.columns(2)
        with c1:
            uploaded_file1 = st.file_uploader("Upload Source A", type=["xlsx", "csv", "json"])
        with c2:
            uploaded_file2 = st.file_uploader("Upload Source B", type=["xlsx", "csv", "json"])

        if uploaded_file1 and uploaded_file2:
            # Read files
            if data_source == "Excel (.xlsx)":
                df1 = pd.read_excel(uploaded_file1)
                df2 = pd.read_excel(uploaded_file2)
            elif data_source == "CSV (.csv)":
                df1 = pd.read_csv(uploaded_file1)
                df2 = pd.read_csv(uploaded_file2)
            elif data_source == "JSON (.json)":
                df1 = pd.read_json(uploaded_file1)
                df2 = pd.read_json(uploaded_file2)
            else:
                st.error("Unsupported format.")
                st.stop()

            st.success("✅ Data loaded successfully!")

            # Preview data
            st.write("### 🔍 Preview Source A")
            st.dataframe(df1.head(), use_container_width=True)
            st.write("### 🔍 Preview Source B")
            st.dataframe(df2.head(), use_container_width=True)

            # Save to DB
            st.markdown("### 💾 Save Data into Database")
            table_a = st.text_input("Enter table name for Source A", "source_a")
            table_b = st.text_input("Enter table name for Source B", "source_b")

            if st.button("💾 Save to Database"):
                try:
                    conn = connect_db(selected_db)
                    df1.to_sql(table_a, conn, if_exists="replace", index=False)
                    df2.to_sql(table_b, conn, if_exists="replace", index=False)
                    conn.close()
                    st.success(f"🎉 Data saved successfully in '{selected_db}' as '{table_a}' and '{table_b}'.")
                except Exception as e:
                    st.error(f"❌ Error saving data: {e}")

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
            st.success("✅ Mapping ready (visual arrows can be added later).")
