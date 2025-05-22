
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import requests
import re
import os

# --- SQLite Database Setup ---
def init_db():
    db_path = os.path.join(os.getcwd(), 'kyra.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            name TEXT,
            role TEXT
        )
    ''')
    
    # Create projects table
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            project_title TEXT,
            timestamp TEXT
        )
    ''')
    
    # Create chat_logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            name TEXT,
            project_title TEXT,
            question TEXT,
            response TEXT,
            timestamp TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# --- Streamlit frontend ---
# Set page configuration with Ky’ra logo
st.set_page_config(
    page_title="Ask Ky’ra",
    page_icon="https://raw.githubusercontent.com/SharmilaGhosh120/app16/main/WhatsApp%20Image%202025-05-20%20at%2015.17.59.jpeg",
    layout="centered"
)

# Custom styling with improved scrollable chat area
st.markdown(
    """
    <style>
    .main {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        font-family: 'Roboto', sans-serif;
    }
    .stTextInput > div > input {
        border: 1px solid #ccc;
        border-radius: 5px;
        font-family: 'Roboto', sans-serif;
    }
    .stTextArea > div > textarea {
        border: 1px solid #ccc;
        border-radius: 5px;
        font-family: 'Roboto', sans-serif;
    }
    .submit-button {
        display: flex;
        justify-content: center;
    }
    .submit-button .stButton > button {
        background-color: #4fb8ac;
        color: white;
        font-size: 18px;
        padding: 10px 20px;
        border-radius: 8px;
        width: 200px;
        font-family: 'Roboto', sans-serif;
    }
    .history-entry {
        padding: 15px;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        background-color: #ffffff;
        margin-bottom: 10px;
        box-shadow: 1px 1px 3px #ccc;
        font-family: 'Roboto', sans-serif;
        word-wrap: break-word;
        overflow-wrap: break-word;
        max-width: 100%;
    }
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        background-color: #f9f9f9;
    }
    .chat-footer {
        text-align: center;
        font-family: 'Roboto', sans-serif;
        color: #4fb8ac;
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header with official Ky’ra logo
try:
    logo_url = "https://raw.githubusercontent.com/SharmilaGhosh120/app16/main/WhatsApp%20Image%202025-05-20%20at%2015.17.59.jpeg"
    st.image(logo_url, width=80, caption="Ky’ra Logo", use_container_width=True, output_format="JPEG")
except Exception as e:
    st.warning(f"Failed to load Ky’ra logo: {str(e)}. Please ensure the logo URL is accessible or use a local file.")

# Initialize session state
if "email" not in st.session_state:
    st.session_state.email = ""
if "name" not in st.session_state:
    st.session_state.name = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "page" not in st.session_state:
    st.session_state.page = 1

# Input fields
st.subheader("Your Details")
email_input = st.text_input("Student Email", placeholder="student123@college.edu", help="Enter your college email address.")
name_input = st.text_input("Your Name", placeholder="Enter your name", help="Enter your full name.")

# Function to validate email
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

# Save user details to SQLite
def save_user(email, name):
    db_path = os.path.join(os.getcwd(), 'kyra.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    role = "admin" if "admin" in email.lower() else "student"
    c.execute('INSERT OR REPLACE INTO users (email, name, role) VALUES (?, ?, ?)', (email, name, role))
    conn.commit()
    conn.close()

# Format timestamp
def format_timestamp(timestamp_str):
    try:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%B %d, %Y %I:%M %p")
    except:
        return timestamp_str

# Role-based dashboards
def show_admin_dashboard(name):
    st.markdown(f"<h1 style='text-align: center; color: #4fb8ac; font-family: \"Roboto\", sans-serif;'>🎓 Welcome College Admin, {name}!</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-family: \"Roboto\", sans-serif;'>Manage student mappings, projects, and reports with Ky’ra.</p>", unsafe_allow_html=True)
    
    # Admin Dashboard: Student Mapping Upload
    st.subheader("Upload Student Mapping")
    uploaded_file = st.file_uploader("Upload a CSV file (student_id,project_title)", type=["csv"])
    if uploaded_file is not None:
        try:
            mapping_df = pd.read_csv(uploaded_file)
            required_columns = ["student_id", "project_title"]
            if not all(col in mapping_df.columns for col in required_columns):
                st.error("CSV must contain 'student_id' and 'project_title' columns.")
            else:
                st.markdown("**Preview of Uploaded Student Mapping:**")
                st.dataframe(mapping_df)
                if st.button("Save Mapping"):
                    db_path = os.path.join(os.getcwd(), 'kyra.db')
                    conn = sqlite3.connect(db_path)
                    c = conn.cursor()
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    for _, row in mapping_df.iterrows():
                        c.execute('INSERT INTO projects (email, project_title, timestamp) VALUES (?, ?, ?)',
                                (row['student_id'], row['project_title'], timestamp))
                    conn.commit()
                    conn.close()
                    st.success("Student mapping saved successfully!")
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    
    # Admin: View project-wise chat logs
    st.subheader("Project-Wise Chat Logs")
    db_path = os.path.join(os.getcwd(), 'kyra.db')
    conn = sqlite3.connect(db_path)
    chat_logs = pd.read_sql_query("SELECT email, name, project_title, question, response, timestamp FROM chat_logs", conn)
    conn.close()
    if not chat_logs.empty:
        for project_title in chat_logs['project_title'].unique():
            with st.expander(f"Chat Logs for Project: {project_title}"):
                project_logs = chat_logs[chat_logs['project_title'] == project_title]
                for _, row in project_logs.iterrows():
                    st.markdown(
                        f"<div class='history-entry'><strong>{row['name']} ({row['email']}) asked:</strong> {row['question']} <i>(submitted at {format_timestamp(row['timestamp'])})</i><br><strong>Ky’ra replied:</strong> {row['response']}</div>",
                        unsafe_allow_html=True
                    )
                    st.markdown("---")
    else:
        st.markdown("<p style='font-family: \"Roboto\", sans-serif;'>No chat logs available.</p>", unsafe_allow_html=True)

def show_student_dashboard(name):
    st.markdown(f"<h1 style='text-align: center; color: #4fb8ac; font-family: \"Roboto\", sans-serif;'>👋 Welcome, {name}!</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-family: \"Roboto\", sans-serif;'>Ask Ky’ra anything about resumes, interviews, or project help - I’ll guide you step-by-step!</p>", unsafe_allow_html=True)
    
    # Student Dashboard: Project Assignment Submission
    st.subheader("Submit Your Project Title")
    project_title = st.text_input("Enter your project title:", placeholder="E.g., AI-based Chatbot for Internship Assistance")
    if st.button("Submit Project"):
        if project_title:
            db_path = os.path.join(os.getcwd(), 'kyra.db')
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute('INSERT INTO projects (email, project_title, timestamp) VALUES (?, ?, ?)',
                    (st.session_state.email, project_title, timestamp))
            conn.commit()
            conn.close()
            st.success("Project title submitted successfully!")
        else:
            st.error("Please enter a project title.")

# Process user input
if email_input and name_input:
    if is_valid_email(email_input):
        save_user(email_input, name_input)
        st.session_state.email = email_input
        st.session_state.name = name_input
        role = "admin" if "admin" in email_input.lower() else "student"
        
        if role == "admin":
            show_admin_dashboard(name_input)
        else:
            show_student_dashboard(name_input)
    else:
        st.error("Please enter a valid email address (e.g., student@college.edu).")
else:
    st.markdown("<h1 style='text-align: center; color: #4fb8ac; font-family: \"Roboto\", sans-serif;'>👋 Ask Ky’ra – Your Internship Assistant</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-family: \"Roboto\", sans-serif;'>Hi! I’m Ky’ra, your internship buddy. Enter your email and name to get started!</p>", unsafe_allow_html=True)

# Query Section (for both roles)
if email_input and name_input:
    st.subheader("Ask Ky’ra a Question")
    sample_questions = [
        "How do I write my internship resume?",
        "What are the best final-year projects in AI?",
        "How can I prepare for my upcoming interview?",
        "What skills should I learn for a career in cybersecurity?"
    ]
    selected_question = st.selectbox("Choose a sample question or type your own:", sample_questions + ["Custom question..."])
    query_text = st.text_area("Your Question", value=selected_question if selected_question != "Custom question..." else "", height=150, placeholder="E.g., How can I prepare for my internship interview?")

# Function to call Ky’ra's backend API
def kyra_response(email, query):
    api_url = "http://kyra.kyras.in:8000/student-query"
    payload = {"student_id": email.strip(), "query": query.strip()}
    try:
        response = requests.post(api_url, params=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get("response", "No response from Ky’ra.")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        st.warning("API is unavailable. Using mock response for testing.")
        return f"Mock response for query: {query} (API unavailable: {str(e)})"

# Function to save queries to SQLite
def save_query(email, name, project_title, question, response, timestamp):
    db_path = os.path.join(os.getcwd(), 'kyra.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT * FROM chat_logs WHERE email = ? AND question = ? AND timestamp = ?', (email, question, timestamp))
    if not c.fetchone():
        c.execute('INSERT INTO chat_logs (email, name, project_title, question, response, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                (email, name, project_title, question, response, timestamp))
        conn.commit()
    conn.close()

# Submit button logic for queries
if email_input and name_input:
    st.markdown('<div class="submit-button">', unsafe_allow_html=True)
    if st.button("Submit", type="primary"):
        if not email_input or not query_text:
            st.error("Please enter both a valid email and a query.")
        elif not is_valid_email(email_input):
            st.error("Please enter a valid email address (e.g., student@college.edu).")
        else:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db_path = os.path.join(os.getcwd(), 'kyra.db')
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute('SELECT project_title FROM projects WHERE email = ? ORDER BY timestamp DESC LIMIT 1', (email_input,))
                result = c.fetchone()
                project_title = result[0] if result else "No Project Assigned"
                conn.close()
                
                response = kyra_response(email_input, query_text)
                save_query(email_input, name_input, project_title, query_text, response, timestamp)
                st.session_state.chat_history.append({
                    "email": email_input,
                    "name": name_input,
                    "query": query_text,
                    "response": response,
                    "timestamp": timestamp
                })
                st.success("Thank you! Ky’ra has received your question and is preparing your guidance.")
                with st.expander("🧠 Ky’ra’s Response", expanded=True):
                    st.markdown(
                        f"<div class='history-entry'><strong>Ky’ra’s Response:</strong><br>{response}</div>",
                        unsafe_allow_html=True
                    )
            except Exception as e:
                st.error(f"Failed to process query: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

# Display paginated chat history
if email_input and name_input:
    st.markdown("**🧾 Your Chat History:**")
    db_path = os.path.join(os.getcwd(), 'kyra.db')
    conn = sqlite3.connect(db_path)
    user_df = pd.read_sql_query("SELECT name, question, response, timestamp FROM chat_logs WHERE email = ? ORDER BY timestamp DESC", conn, params=(email_input,))
    conn.close()
    
    if not user_df.empty:
        user_df = user_df.drop_duplicates(subset=['question', 'timestamp'])
        items_per_page = 5
        total_pages = (len(user_df) + items_per_page - 1) // items_per_page
        st.session_state.page = max(1, min(st.session_state.page, total_pages))
        
        start_idx = (st.session_state.page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_df = user_df.iloc[start_idx:end_idx]
        
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for idx, row in paginated_df.iterrows():
            response_text = row['response'] if pd.notna(row['response']) else "No response available."
            with st.expander(f"Question from {format_timestamp(row['timestamp'])}"):
                st.markdown(
                    f"<div class='history-entry'><strong>You asked:</strong> {row['question']} <i>(submitted at {format_timestamp(row['timestamp'])})</i><br><strong>Ky’ra replied:</strong> {response_text}</div>",
                    unsafe_allow_html=True
                )
                st.markdown("---")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("Previous", disabled=st.session_state.page == 1):
                st.session_state.page -= 1
        with col3:
            if st.button("Next", disabled=st.session_state.page == total_pages):
                st.session_state.page += 1
        with col2:
            st.write(f"Page {st.session_state.page} of {total_pages}")
    else:
        st.markdown("<p style='font-family: \"Roboto\", sans-serif;'>No chat history yet. Ask Ky’ra a question to get started!</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# Display project submissions (for students)
if email_input and name_input and "admin" not in email_input.lower():
    st.subheader("Your Submitted Projects")
    db_path = os.path.join(os.getcwd(), 'kyra.db')
    conn = sqlite3.connect(db_path)
    user_projects = pd.read_sql_query("SELECT project_title, timestamp FROM projects WHERE email = ? ORDER BY timestamp DESC", conn, params=(email_input,))
    conn.close()
    if not user_projects.empty:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for idx, row in user_projects.iterrows():
            st.markdown(
                f"<div class='history-entry'><strong>Project Title:</strong> {row['project_title']} <i>(submitted at {format_timestamp(row['timestamp'])})</i></div>",
                unsafe_allow_html=True
            )
            st.markdown("---")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("<p style='font-family: \"Roboto\", sans-serif;'>No projects submitted yet.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# Footer
st.markdown(
    "<p class='chat-footer'>Ky’ra is here whenever you need. Ask freely. Grow boldly.</p>",
    unsafe_allow_html=True
)

# Storage notice
st.markdown("Your chat history and project submissions are securely stored to help Ky’ra guide you better next time.", unsafe_allow_html=True)
