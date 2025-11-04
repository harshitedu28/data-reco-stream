import streamlit as st
import pandas as pd
import sqlite3
import os

# -----------------------------------------------
# APP CONFIG
# -----------------------------------------------
st.set_page_config(page_title="🧩 Smart Reconciliation Suite", layout="wide")
st.markdown("<h1 style='text-align:center;'>🧮 Smart Reconciliation Platform</h1>", unsafe_allow_html=True)

# -----------------------------------------------
# UTILITIES
# -----------------------------------------------
DB_DIR = "databases"
os.makedirs(DB_DIR, exist_ok=True)

def list_databases():
    """List available SQLite database files."""
    return [f for f in os.listdir(DB_DIR) if f.endswith(".db")]

def create_database(db_name):
    """Create new SQLite database file."""
    db_path = os.path.join(DB_DIR, f"{db_name}.db")
    conn = sqlite3.connect(db_path)
    conn.close()
    return db_path

def connect_db(db_name):
    """Connect to a specific database."""
    db_path = os.path.join(DB_DIR, db_name)
    return sqlite3.connect(db_path)

# -----------------------------------------------
# SIDEBAR MENU
# -----------------------------------------------
st.sidebar.title("📋 Navigation Menu")

module = st.sidebar.radio(
    "Select Module",
    ["🏠 Dashboard", "📂 Data Source", "🗄 Database", "🔗 Mapping"],
    index=0
)

# -----------------------------------------------
# MODULE 1: DASHBOARD (placeholder)
# -----------------------------------------------
if module == "🏠 Dashboard":
    st.subheader("📊 Dashboard Overview (Coming Soon)")
    st.info("This module will show reconciliation summary, success rates, logs, and recent mappings.")


# -----------------------------------------------
# MODULE 2: DATA SOURCE
# -----------------------------------------------
elif module == "📂 Data Source":
    st.subheader("📂 Data Source Module")
    st.write("Import your data from various formats and store it into a database for mapping & reconciliation.")

    # Step 1: Choose Data Source Type
    data_source = st.selectbox(
        "Select Data Source Type",
        ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)", "SQL Query (coming soon)", "API Endpoint (coming soon)"]
    )

    # Step 2: Choose Target Database
    st.markdown("### 🗄 Select Target Database to Store Imported Data")
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
        selected_db = st.selectbox("Select existing database", available_dbs)

        # Step 3: Upload Files
        st.markdown("### 📥 Upload Files")
        c1, c2 = st.columns(2)
        with c1:
            uploaded_a = st.file_uploader("Upload Source A", type=["csv", "xlsx", "json"])
        with c2:
            uploaded_b = st.file_uploader("Upload Source B", type=["csv", "xlsx", "json"])

        # Step 4: Load & Save Data
        if uploaded_a and uploaded_b:
            if data_source == "Excel (.xlsx)":
                df_a = pd.read_excel(uploaded_a)
                df_b = pd.read_excel(uploaded_b)
            elif data_source == "CSV (.csv)":
                df_a = pd.read_csv(uploaded_a)
                df_b = pd.read_csv(uploaded_b)
            elif data_source == "JSON (.json)":
                df_a = pd.read_json(uploaded_a)
                df_b = pd.read_json(uploaded_b)
            else:
                st.error("Unsupported format for now.")
                st.stop()

            st.success("✅ Data loaded successfully!")

            st.write("### 🔍 Source A Preview")
            st.dataframe(df_a.head(), use_container_width=True)
            st.write("### 🔍 Source B Preview")
            st.dataframe(df_b.head(), use_container_width=True)

            # Save to DB
            table_a = st.text_input("Enter table name for Source A", "source_a")
            table_b = st.text_input("Enter table name for Source B", "source_b")

            if st.button("💾 Save to Database"):
                try:
                    conn = connect_db(selected_db)
                    df_a.to_sql(table_a, conn, if_exists="replace", index=False)
                    df_b.to_sql(table_b, conn, if_exists="replace", index=False)
                    conn.close()
                    st.success(f"🎉 Data saved to '{selected_db}' successfully!")
                except Exception as e:
                    st.error(f"Error saving to DB: {e}")


# -----------------------------------------------
# MODULE 3: DATABASE MANAGEMENT
# -----------------------------------------------
elif module == "🗄 Database":
    st.subheader("🗄 Database Management Module")
    st.write("Create, view, or manage multiple databases to store imported data.")

    existing_dbs = list_databases()
    st.markdown("### 📋 Existing Databases")
    if existing_dbs:
        st.table(pd.DataFrame({"Databases": existing_dbs}))
    else:
        st.info("No databases created yet.")

    st.markdown("---")
    st.markdown("### ➕ Create New Database")
    new_db_name = st.text_input("Enter new database name (without extension)")
    if st.button("Create Database"):
        if new_db_name.strip():
            db_path = create_database(new_db_name)
            st.success(f"✅ Database '{new_db_name}.db' created successfully at {db_path}")
        else:
            st.warning("Please enter a valid name.")


# -----------------------------------------------
# MODULE 4: MAPPING DESIGN
# -----------------------------------------------
elif module == "🔗 Mapping":
    st.subheader("🔗 Mapping Module (Visual Design)")

    st.write("""
    Here you can design mappings between columns of Source A and Source B.
    Both sides show column names; you can visually map them via selection or connection arrows.
    """)

    # Select DB and Tables
    available_dbs = list_databases()
    if not available_dbs:
        st.warning("⚠️ No database found. Please create one first in the Database Module.")
    else:
        selected_db = st.selectbox("Select database", available_dbs)
        conn = connect_db(selected_db)
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)["name"].tolist()

        if len(tables) < 2:
            st.warning("You need at least two tables to create mapping.")
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

            # Field Mapping UI
            st.markdown("### ⚙️ Field Mapping Design")

            mapping = {}
            for col in df_a.columns:
                mapped_to = st.selectbox(f"{col} →", ["-- None --"] + list(df_b.columns), key=f"map_{col}")
                if mapped_to != "-- None --":
                    mapping[col] = mapped_to

            st.json(mapping)

            st.success("✅ Mapping structure ready! (Visual linking arrows can be added in next enhancement)")
