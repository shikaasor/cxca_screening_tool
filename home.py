from utils.tools import set_background
import streamlit as st
from supabase import create_client
import os
from datetime import datetime

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def init_session_state():
    """Initialize session state variables if they don't exist"""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "facility" not in st.session_state:
        st.session_state.facility = None
    if "login_time" not in st.session_state:
        st.session_state.login_time = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "username" not in st.session_state:
        st.session_state.username = None

def check_active_session():
    """Check if there's an active Supabase session"""
    try:
        session = supabase.auth.get_session()
        if session:
            return session.user
        return None
    except Exception:
        return None

def get_user_metadata(user_id):
    """Fetch user metadata from Supabase"""
    try:
        response = supabase.table('profiles').select('username','email','facility').eq('id', user_id).single().execute()
        print(response.data)
        return response.data if response.data else None
    except Exception as e:
        st.error(f"Error fetching user metadata: {str(e)}")
        return None

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
        st.success("Logged out successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error during logout: {str(e)}")

def main():
    st.set_page_config(
        page_title="Cervical Cancer Screening Portal",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    set_background('./bgs/654.jpg')

    init_session_state()
    
    # Check for active session on page load
    if not st.session_state.logged_in:
        user = check_active_session()
        if user:
            user_metadata = get_user_metadata(user.id)
            st.session_state.logged_in = True
            st.session_state.user_id = user.id
            st.session_state.user_email = user_metadata.get('email') if user_metadata else None
            st.session_state.username = user_metadata.get('username') if user_metadata else None
            st.session_state.facility = user_metadata.get('facility') if user_metadata else None
            st.session_state.login_time = datetime.now()
    
    st.title("Welcome to the Cervical Cancer Screening Portal")
    
    # Create three columns for better layout
    left_col, middle_col, right_col = st.columns([1, 2, 1])
    
    with middle_col:
        if st.session_state.logged_in:
            st.write("### Welcome back! 👋")
            st.write(f"You are logged in as: **{st.session_state.username}**")
            st.write(f"Facility: **{st.session_state.facility}**")
            
            # Add a divider
            st.divider()
            
            # Quick actions section
            st.write("### Quick Actions")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Start New Screening", use_container_width=True):
                    # Add navigation to screening page
                    st.switch_page("pages/3_Screening.py")
            
            with col2:
                if st.button("View Records", use_container_width=True):
                    # Add navigation to records page
                    st.switch_page("pages/records.py")
            
            # Logout button at the bottom
            st.divider()
            if st.button("Logout", type="secondary", use_container_width=True):
                logout()
        
        else:
            st.write("### Welcome to the Portal 👋")
            st.write("""
            This portal provides tools for cervical cancer screening and management. 
            Please log in or register to access the system.
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Login", use_container_width=True):
                    st.switch_page("pages/1_Login.py")
            
            with col2:
                if st.button("Register", use_container_width=True):
                    st.switch_page("pages/2_Register.py")
            
            # Add information for new users
            st.divider()
            st.write("### New to the Portal?")
            st.write("""
            Our system helps healthcare providers manage cervical cancer screening efficiently:
            - Record and track screening results
            - Manage patient records
            - Generate reports and analytics
            - Follow up with patients
            
            Register now to get started!
            """)

if __name__ == "__main__":
    main()