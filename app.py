import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

# Set page configuration
st.set_page_config(
    page_title="Task Manager",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to make the UI more beautiful
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .st-emotion-cache-1v0mbdj {
        width: 100%;
    }
    .task-container {
        padding: 1rem;
        border-radius: 10px;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
    }
    div[data-testid="stToolbar"] {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    """Returns `True` if the user had the correct password."""
    
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
        
    if st.session_state.password_correct:
        return True

    st.title("🔐 Task Manager Login")
    st.write("Enter the password to access the Task Manager app.")
    
    password = st.text_input("Password", type="password")
    
    # Try to get password from environment variable first, then from secrets.toml
    correct_password = os.environ.get('STREAMLIT_APP_PASSWORD')
    if not correct_password and 'STREAMLIT_APP_PASSWORD' in st.secrets:
        correct_password = st.secrets['STREAMLIT_APP_PASSWORD']
    
    if not correct_password:
        st.error("⚠️ No password configured! Set STREAMLIT_APP_PASSWORD in environment or secrets.toml")
        return False
    
    if password:
        if password == correct_password:
            st.session_state.password_correct = True
            st.rerun()
            return True
        else:
            st.error("😕 Password incorrect")
            return False
    return False

if check_password():
    # Initialize session state for tasks
    if 'tasks' not in st.session_state:
        st.session_state.tasks = []

    # Load tasks from file if it exists
    TASKS_FILE = "tasks.json"
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            st.session_state.tasks = json.load(f)

    # Main title with emoji
    st.title("✨ Task Manager")
    st.markdown("---")

    # Sidebar for adding new tasks
    with st.sidebar:
        st.header("Add New Task")
        task_name = st.text_input("Task Name")
        priority = st.select_slider(
            "Priority",
            options=["Low", "Medium", "High"],
            value="Medium"
        )
        due_date = st.date_input("Due Date")
        
        if st.button("Add Task", type="primary"):
            if task_name:
                new_task = {
                    "name": task_name,
                    "priority": priority,
                    "due_date": due_date.strftime("%Y-%m-%d"),
                    "completed": False,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.tasks.append(new_task)
                # Save tasks to file
                with open(TASKS_FILE, "w") as f:
                    json.dump(st.session_state.tasks, f)
                st.success("Task added successfully!")
            else:
                st.error("Please enter a task name!")

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📝 Your Tasks")
        
        # Filter tasks
        filter_status = st.radio(
            "Filter by status:",
            ["All", "Active", "Completed"],
            horizontal=True
        )
        
        # Display tasks
        for idx, task in enumerate(st.session_state.tasks):
            if filter_status == "Active" and task["completed"]:
                continue
            if filter_status == "Completed" and not task["completed"]:
                continue
                
            with st.container():
                col_check, col_content, col_actions = st.columns([0.1, 0.7, 0.2])
                
                with col_check:
                    completed = st.checkbox("", task["completed"], key=f"check_{idx}")
                    if completed != task["completed"]:
                        st.session_state.tasks[idx]["completed"] = completed
                        with open(TASKS_FILE, "w") as f:
                            json.dump(st.session_state.tasks, f)
                
                with col_content:
                    if task["completed"]:
                        st.markdown(f"~~{task['name']}~~")
                    else:
                        st.markdown(f"**{task['name']}**")
                    st.caption(f"Due: {task['due_date']} | Priority: {task['priority']}")
                
                with col_actions:
                    if st.button("Delete", key=f"del_{idx}"):
                        st.session_state.tasks.pop(idx)
                        with open(TASKS_FILE, "w") as f:
                            json.dump(st.session_state.tasks, f)
                        st.rerun()

    with col2:
        st.subheader("📊 Statistics")
        
        # Convert tasks to DataFrame for analysis
        df = pd.DataFrame(st.session_state.tasks)
        
        if not df.empty:
            # Priority distribution
            priority_counts = df['priority'].value_counts()
            fig_priority = px.pie(
                values=priority_counts.values,
                names=priority_counts.index,
                title="Tasks by Priority",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_priority, use_container_width=True)
            
            # Completion status
            completion_counts = df['completed'].value_counts()
            fig_completion = px.pie(
                values=completion_counts.values,
                names=['Completed', 'Active'] if True in completion_counts.index else ['Active'],
                title="Completion Status",
                color_discrete_sequence=['#00CC96', '#EF553B']
            )
            st.plotly_chart(fig_completion, use_container_width=True)
        else:
            st.info("Add some tasks to see statistics!") 
