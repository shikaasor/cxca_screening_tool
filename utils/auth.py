import streamlit as st
from datetime import datetime, timedelta

def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'facility' not in st.session_state:
        st.session_state.facility = None
    if 'login_time' not in st.session_state:
        st.session_state.login_time = None
    if 'approved' not in st.session_state:
        st.session_state.approved = None

def check_auth():
    if not st.session_state.logged_in:
        st.warning("Please log in to access this page")
        st.switch_page("pages/1_Login.py")
    
    # Check session timeout (4 hours)
    if st.session_state.login_time:
        if datetime.now() - st.session_state.login_time > timedelta(hours=4):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.facility = None
            st.session_state.login_time = None
            st.warning("Session expired. Please log in again")
            st.stop()