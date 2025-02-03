import streamlit as st
from supabase import create_client
import os
from utils.tools import set_background
from utils.auth import check_auth

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def fetch_pending_reviewers():
    """Fetch all pending reviewer users from the profiles table"""
    try:
        response = supabase.table("profiles").select("*").eq("user_category", "reviewer").eq("approved", False).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching pending reviewers: {str(e)}")
        return []

def approve_reviewer(user_id):
    """Approve a reviewer user by updating the approved field to True"""
    try:
        response = supabase.table("profiles").update({"approved": True}).eq("id", user_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error approving reviewer: {str(e)}")
        return None

def admin_page():
    st.set_page_config(
        page_title="Admin Dashboard",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    set_background('./bgs/654.jpg')
    
    # Check authentication and admin status
    check_auth()
    if st.session_state.get("user_category") != "admin":
        st.error("You do not have permission to access this page.")
        st.stop()

    st.markdown("<h1 style='text-align: center; color: #A5FFFD; border: 2px solid #30B0C2; border-radius: 10px; padding: 10px;'>Admin Dashboard</h1>", unsafe_allow_html=True)

    # Fetch and display pending reviewers
    pending_reviewers = fetch_pending_reviewers()
    if not pending_reviewers:
        st.info("No pending reviewers found.")
        return

    st.write("### Pending Reviewers")
    for reviewer in pending_reviewers:
        with st.container():
            st.write(f"**Username:** {reviewer['username']}")
            st.write(f"**Email:** {reviewer['email']}")
            if st.button(f"Approve {reviewer['username']}", key=f"approve_{reviewer['id']}"):
                approve_reviewer(reviewer['id'])
                st.success(f"Approved {reviewer['username']}!")
                st.rerun()

if __name__ == "__main__":
    admin_page()