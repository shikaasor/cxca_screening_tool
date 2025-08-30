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

def inject_custom_css():
    """Inject minimal custom CSS for clean visual design"""
    st.markdown("""
    <style>
    /* Background overlay for better readability */
    .main > div {
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(5px);
        border-radius: 8px;
        padding: 2rem;
        margin: 1rem;
    }
    
    /* Clean typography */
    h1 {
        color: #2c3e50;
        font-weight: 600;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    h3 {
        color: #34495e;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    
    /* Elegant button styling */
    .stButton > button {
        background: #3498db;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: background-color 0.2s ease;
    }
    
    .stButton > button:hover {
        background: #2980b9;
    }
    
    .stButton > button[kind="secondary"] {
        background: #95a5a6;
        color: white;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #7f8c8d;
    }
    
    /* Clean user info styling */
    .user-info {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 6px;
        border-left: 4px solid #3498db;
        margin: 1rem 0;
    }
    
    /* Subtle dividers */
    hr {
        border: none;
        border-top: 1px solid #ecf0f1;
        margin: 2rem 0;
    }
    
    /* Clean sidebar styling */
    .sidebar .sidebar-content {
        background: rgba(255, 255, 255, 0.95);
    }
    </style>
    """, unsafe_allow_html=True)

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
    if "user_category" not in st.session_state:
        st.session_state.user_category = None
    if "approved" not in st.session_state:
        st.session_state.approved = None

@st.cache_data(ttl=300)
def check_active_session():
    """Check if there's an active Supabase session"""
    try:
        session = supabase.auth.get_session()
        if session:
            return session.user
        return None
    except Exception:
        return None

@st.cache_data(ttl=600)
def get_user_metadata(user_id):
    """Fetch user metadata from Supabase"""
    try:
        with st.spinner("Loading..."):
            response = supabase.table('profiles').select('username','email','facility','user_category','approved').eq('id', user_id).single().execute()
            return response.data if response.data else None
    except Exception as e:
        st.error(f"Error fetching user data: {str(e)}")
        return None

def logout():
    """Sign out the user from Supabase and clear session state"""
    try:
        with st.spinner("Signing out..."):
            supabase.auth.sign_out()
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.facility = None
            st.session_state.login_time = None
            st.session_state.user_email = None
            st.session_state.username = None
            st.session_state.approved = None
            st.success("Successfully logged out")
            st.rerun()
    except Exception as e:
        st.error(f"Error during logout: {str(e)}")

def main():
    st.set_page_config(
        page_title="Cervical Cancer Screening Portal",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="auto"
    )
    
    # Apply styling and background
    inject_custom_css()
    set_background('./bgs/654.jpg')
    init_session_state()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### Navigation")
        if st.session_state.logged_in:
            st.info(f"Logged in as: **{st.session_state.username}**")
            if st.button("New Screening", use_container_width=True):
                st.switch_page("pages/3_Screening.py")
            if st.session_state.user_category == "reviewer" and st.session_state.approved:
                if st.button("View Records", use_container_width=True):
                    st.switch_page("pages/4_records.py")
        else:
            if st.button("Login", use_container_width=True):
                st.switch_page("pages/1_Login.py")
            if st.button("Register", use_container_width=True):
                st.switch_page("pages/2_Register.py")
    
    # Check for active session
    if not st.session_state.logged_in:
        user = check_active_session()
        if user:
            user_metadata = get_user_metadata(user.id)
            if user_metadata:
                st.session_state.logged_in = True
                st.session_state.user_id = user.id
                st.session_state.user_email = user_metadata.get('email')
                st.session_state.username = user_metadata.get('username')
                st.session_state.facility = user_metadata.get('facility')
                st.session_state.user_category = user_metadata.get('user_category')
                st.session_state.approved = user_metadata.get('approved')
                st.session_state.login_time = datetime.now()
                st.rerun()
    
    # Main content
    st.title("Cervical Cancer Screening Portal")
    
    # Center column for main content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.session_state.logged_in:
            # User dashboard
            st.markdown("### Welcome back")
            
            st.markdown(f"""
            <div class="user-info">
                <strong>{st.session_state.username}</strong><br>
                {st.session_state.facility}<br>
                <small>{st.session_state.user_email}</small>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Action buttons
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("Start New Screening", use_container_width=True, help="Begin a new screening session"):
                    st.switch_page("pages/3_Screening.py")
            
            with col_b:
                if st.session_state.user_category == "reviewer" and st.session_state.approved:
                    if st.button("View Records", use_container_width=True, help="Access patient records"):
                        st.switch_page("pages/4_records.py")
                else:
                    st.button("View Records", use_container_width=True, disabled=True, 
                             help="Requires reviewer privileges and approval")
            
            st.markdown("---")
            
            # Logout
            if st.button("Logout", type="secondary", use_container_width=True):
                logout()
        
        else:
            # Welcome screen
            st.markdown("### Welcome")
            st.write("""
            This portal provides tools for cervical cancer screening and management. 
            Please log in or register to access the system.
            """)
            
            # Login/Register buttons
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("Login", use_container_width=True, help="Sign in to your account"):
                    st.switch_page("pages/1_Login.py")
            
            with col_b:
                if st.button("Register", use_container_width=True, help="Create a new account"):
                    st.switch_page("pages/2_Register.py")
            
            # Additional info
            with st.expander("About this portal"):
                st.write("""
                **Features:**
                - Record and track screening results
                - Manage patient records  
                - Generate reports and analytics
                - Follow up with patients
                
                Register now to get started.
                """)

if __name__ == "__main__":
    main()