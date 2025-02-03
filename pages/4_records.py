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

def fetch_screening_records():
    """Fetch all screening records from the Supabase table"""
    try:
        response = supabase.table("screenings").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching screening records: {str(e)}")
        return []

def logout():
    """Sign out the user from Supabase and clear session state"""
    try:
        supabase.auth.sign_out()
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.facility = None
        st.session_state.login_time = None
        st.session_state.user_email = None
        st.session_state.username = None
        st.session_state.approved = None
        st.success("Logged out successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error during logout: {str(e)}")

def records_page():
    st.set_page_config(
        page_title="Screening Records",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    set_background('./bgs/654.jpg')
    
    # Check authentication and user category
    check_auth()
    if st.session_state.get("user_category") != "reviewer" and st.session_state.approved:
        st.error("You do not have permission to access this page.")
        st.stop()

    st.markdown("<h1 style='text-align: center; color: #A5FFFD; border: 2px solid #30B0C2; border-radius: 10px; padding: 10px;'>Screening Records</h1>", unsafe_allow_html=True)

    # Fetch and display records
    records = fetch_screening_records()
    if not records:
        st.info("No screening records found.")
        return

    # Display records in a table
    st.dataframe(
        records,
        use_container_width=True,
        column_config={
            "image_url": st.column_config.ImageColumn("Image", help="Screened Image"),
            "diagnosis": st.column_config.TextColumn("Diagnosis"),
            "confidence_score": st.column_config.ProgressColumn(
                "Confidence Score",
                format="%.2f%%",
                min_value=0,
                max_value=1,
            ),
            "facility": st.column_config.TextColumn("Facility"),
            "client_code": st.column_config.TextColumn("Client Code"),
            "created_at": st.column_config.DatetimeColumn("Screened At"),
        },
    )

    # Logout button at the bottom
    st.divider()
    if st.button("Logout", type="secondary", use_container_width=True):
        logout()

if __name__ == "__main__":
    records_page()