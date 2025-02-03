from utils.tools import set_background
import streamlit as st
from supabase import create_client
from datetime import datetime
import os

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
    if "username" not in st.session_state:
        st.session_state.username = None
    if "facility" not in st.session_state:
        st.session_state.facility = None
    if "login_time" not in st.session_state:
        st.session_state.login_time = None

def get_user_metadata(user_id):
    """Fetch user metadata from Supabase"""
    try:
        response = supabase.table('profiles').select('username','email','facility').eq('id', user_id).single().execute()
        return response.data if response.data else None
    except Exception as e:
        st.error(f"Error fetching user metadata: {str(e)}")
        return None


def login_page():
    st.set_page_config(initial_sidebar_state="collapsed")
    st.markdown("<h1 style='text-align: center; color: #A5FFFD; border: 2px solid #30B0C2; border-radius: 10px; padding: 10px;'>Cervical Cancer Screening Tool</h1>", unsafe_allow_html=True)
    st.title("Login")
    
    set_background('./bgs/654.jpg')

    init_session_state()
    
    if st.session_state.logged_in:
        st.success("You are already logged in!")
        st.switch_page("home.py")
        return
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if email and password:
            try:
                # Attempt to sign in with Supabase
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                # Get user data from response
                user = response.user
                
                if user:
                    # Fetch user metadata (like facility)
                    user_metadata = get_user_metadata(user.id)
                    
                    # Update session state
                    st.session_state.logged_in = True
                    st.session_state.user_id = user.id
                    st.session_state.username = user_metadata.get('username') if user_metadata else None
                    st.session_state.facility = user_metadata.get('facility') if user_metadata else None
                    st.session_state.login_time = datetime.now()
                    
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")
                    
            except Exception as e:
                st.error(f"Login failed: {str(e)}")
        else:
            st.error("Please fill in all fields")

def logout():
    """Sign out the user from Supabase and clear session state"""
    try:
        supabase.auth.sign_out()
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.facility = None
        st.session_state.login_time = None
        st.success("Logged out successfully!")
    except Exception as e:
        st.error(f"Error during logout: {str(e)}")

if __name__ == "__main__":
    login_page()