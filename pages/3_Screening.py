import streamlit as st
from utils.supabase_utils import init_supabase, save_image_to_supabase, save_screening_data
from utils.email_utils import send_to_clinician
from PIL import Image
import os
import torch
from ultralytics import YOLO
from utils.auth import check_auth
from utils.tools import classify, set_background
from dotenv import load_dotenv

# Load environment variables and initialize Supabase
load_dotenv()
supabase = init_supabase()

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

# Main function
def screening_page():
    st.set_page_config(initial_sidebar_state="collapsed")
    set_background('./bgs/654.jpg')
    check_auth()
    
    st.markdown("<h1 style='text-align: center; color: #A5FFFD; border: 2px solid #30B0C2; border-radius: 10px; padding: 10px;'>Cervical Cancer Screening Tool</h1>", unsafe_allow_html=True)

    st.write(f"User: {st.session_state.username}")
    st.write(f"Facility: {st.session_state.facility}")

    st.markdown("<h2 style='text-align: center;'>Please upload an image for analysis</h2>", unsafe_allow_html=True)

    # Initialize session state
    if 'screening_data' not in st.session_state:
        st.session_state.screening_data = {
            'image': None,
            'diagnosis': None,
            'client_code': None
        }

    # Upload file
    file = st.file_uploader(label='Upload image for screening', type=['jpeg', 'jpg', 'png'])

    # Load model
    try:
        model = YOLO("./model/best.pt")
        model.to(torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        st.stop()

    # Process image
    if st.button("Screen") and file is not None:
        image = Image.open(file).convert('RGB')
        st.image(image, use_column_width=False, width=400, caption='Uploaded Image')

        class_name, conf_score = classify(image, model)
        st.session_state.screening_data.update({
            'image': image,
            'diagnosis': {'class_name': class_name, 'conf_score': conf_score}
        })

        st.subheader(f"Diagnosis: {class_name}")
        st.write(f"Confidence Score: {conf_score:.2%}")

        if conf_score < 0.9:
            st.warning("Confidence score is below 90%. Consider escalating to a clinician.")

    # Escalate to clinician
    if (st.session_state.screening_data['diagnosis'] is not None and 
        st.session_state.screening_data['diagnosis']['conf_score'] < 0.9):
        
        client_code = st.text_input("Client_Code", placeholder="Please enter the client code")
        st.session_state.screening_data['client_code'] = client_code

        if st.button("Escalate to Clinician", key="escalate_button"):
            with st.spinner("Sending to clinician..."):
                image_url = save_image_to_supabase(supabase, file, client_code)
                save_screening_data(
                    supabase,
                    image_url,
                    st.session_state.screening_data['diagnosis']['class_name'],
                    st.session_state.screening_data['diagnosis']['conf_score'],
                    st.session_state.facility,
                    client_code
                )
                
                if send_to_clinician(
                    st.session_state.screening_data['image'], 
                    st.session_state.screening_data['diagnosis']['class_name'],
                    st.session_state.screening_data['diagnosis']['conf_score'],
                    st.session_state.facility,
                    client_code
                ):
                    st.success("Successfully sent to clinician for review!")
                    st.session_state.screening_data = {'image': None, 'diagnosis': None, 'client_code': None}
                else:
                    st.error("Failed to send to clinician. Please try again or contact support.")
    # Logout button at the bottom
    st.divider()
    if st.button("Logout", type="secondary", use_container_width=True):
        logout()
        
if __name__ == "__main__":
    screening_page()