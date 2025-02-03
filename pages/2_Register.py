import streamlit as st
from dotenv import load_dotenv
import os
import re
from supabase import create_client
from utils.tools import set_background

# Initialize Supabase client
load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def get_facilities():
    """Get list of facilities from environment variables"""
    facilities_str = st.secrets.get('FACILITIES', os.getenv('FACILITIES'))
    if not facilities_str:
        return []
    return [facility.strip() for facility in facilities_str.split(',')]

def create_user_profile(user_id, username, email, facility, user_category):
    """Create user profile in Supabase after successful registration"""
    try:
        profile_data = {
            "id": user_id,
            "username": username,
            "email": email,
            "user_category": user_category,
            "facility": facility if user_category == "service_provider" else None
        }
        
        response = supabase.table('profiles').insert(profile_data).execute()
        return response.data
    except Exception as e:
        raise Exception(f"Failed to create user profile: {str(e)}")

def register_page():
    st.set_page_config(initial_sidebar_state="collapsed")
    st.markdown("<h1 style='text-align: center; color: #A5FFFD; border: 2px solid #30B0C2; border-radius: 10px; padding: 10px;'>Cervical Cancer Screening Tool</h1>", unsafe_allow_html=True)
    st.title("Register")

    set_background('./bgs/654.jpg')
    
    # Create two columns for layout
    col1, col2 = st.columns(2)
    
    with col1:
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
    
    with col2:
        confirm_password = st.text_input("Confirm Password", type="password")
        user_category = st.selectbox(
            "User Category",
            options=["service_provider", "reviewer"],
            format_func=lambda x: "Service Provider" if x == "service_provider" else "Reviewer"
        )
        
        # Show facility field for service providers
        facility = None
        if user_category == "service_provider":
            FACILITIES = get_facilities()
            if not FACILITIES:
                st.error("No facilities have been configured. Please contact administrator")
            else:
                facility = st.selectbox(
                    "Facility", 
                    options=FACILITIES, 
                    index=None, 
                    placeholder="Choose your facility...",
                    help="Required for service providers"
                )
    
    # Center the register button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        register_button = st.button("Register", use_container_width=True)
    
    if register_button:
        # Validate fields
        if not all([username, email, password, confirm_password]):
            st.error("Please fill in all required fields")
            return
        
        if user_category == "service_provider" and not facility:
            st.error("Facility is required for service providers")
            return
        
        if password != confirm_password:
            st.error("Passwords do not match")
            return
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.error("Invalid email format")
            return
        
        # Password validation
        if len(password) < 8:
            st.error("Password must be at least 8 characters long")
            return
        
        if not any(c.isupper() for c in password):
            st.error("Password must contain at least one uppercase letter")
            return
            
        if not any(c.islower() for c in password):
            st.error("Password must contain at least one lowercase letter")
            return
            
        if not any(c.isdigit() for c in password):
            st.error("Password must contain at least one number")
            return
        
        try:
            # Register user with Supabase Auth
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            # Create user profile
            user_id = auth_response.user.id
            create_user_profile(user_id, username, email, facility, user_category)
            
            st.success("Registration successful! Please check your email to verify your account.")
            
            # Add login button
            if st.button("Go to Login"):
                st.switch_page("pages/1_Login.py")
                
        except Exception as e:
            error_msg = str(e).lower()
            if "already exists" in error_msg and "user" in error_msg:
                st.error("Email already registered")
            elif "already exists" in error_msg and "username" in error_msg:
                st.error("Username already taken")
            else:
                st.error(f"Registration failed: {str(e)}")

if __name__ == "__main__":
    register_page()