import streamlit as st
from ultralytics import YOLO
from PIL import Image
import os
import torch
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
from datetime import datetime
from supabase import create_client, Client
from utils.auth import check_auth
from utils.tools import classify, set_background

load_dotenv()

# Initialize Supabase client
def init_supabase():
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    return create_client(supabase_url, supabase_key)

def get_facilities():
    load_dotenv()
    facilities_str = st.secrets.get('FACILITIES', os.getenv('FACILITIES'))
    if not facilities_str:
        return []
    return [facility.strip() for facility in facilities_str.split(',')]

def save_image_to_supabase(supabase: Client, file, client_code):
    """Save the PIL image to Supabase storage and return the URL"""
    temp_path = "temp_image.jpg"
    image = Image.open(file).convert('RGB')
    image.save(temp_path)
    
    bucket_name = "screening_images"
    file_extension = file.name.split(".")[-1].lower()
    file_path = f"{client_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"

    mime_type_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }

    mime_type = mime_type_map.get(file_extension, "application/octet-stream")
    
    with open(temp_path, 'rb') as f:
        supabase.storage.from_(bucket_name).upload(file_path, f, file_options={"content-type": mime_type})
    
    os.remove(temp_path)
    
    return supabase.storage.from_(bucket_name).get_public_url(file_path)

def save_screening_data(supabase: Client, image_url, class_name, conf_score, selected_facility, client_code):
    """Save screening data to Supabase table"""
    data = {
        "image_url": image_url,
        "diagnosis": class_name,
        "confidence_score": conf_score,
        "facility": selected_facility,
        "client_code": client_code,
        "created_at": datetime.now().isoformat()
    }
    supabase.table("screenings").insert(data).execute()

def send_to_clinician(image, class_name, conf_score, selected_facility, client_code):
    """Send image and details to clinician via email"""
    subject = "Diagnosis Escalation"
    body = f"URGENT REVIEW NEEDED\nFacility: {selected_facility}\nClient Code: {client_code}\nDiagnosis: {class_name}\nConfidence Score: {conf_score:.2%}\nPlease review the attached image."
    
    # get environment variables
    sender_email = os.getenv('SENDER_EMAIL')
    recipient_email = os.getenv('RECIPIENT_EMAIL')
    sender_password = os.getenv('GOOGLE_APP_PASSWORD')

    # smtp server details
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    
    temp_path = "temp_image.jpg"
    image.save(temp_path)

    # construct email
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = recipient_email

    # add body
    body_part = MIMEText(body)
    message.attach(body_part)

    # attach image
    with open(temp_path, 'rb') as file:
        attachment = MIMEApplication(file.read(), Name="Image.jpg")
        attachment['Content-Disposition'] = 'attachment; filename="Image.jpg"'
        message.attach(attachment)
    try:
        # Send message and image via email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        success = True
    except Exception as e:
        success = False
        st.error(f"Error sending to clinician: {str(e)}")
        import traceback
        st.error(f"Detailed error: {traceback.format_exc()}")
    
    # Clean up temporary file
    if os.path.exists(temp_path):
        os.remove(temp_path)
        st.write("Temporary file cleaned up")
    
    return success

def screening_page():
    st.set_page_config(initial_sidebar_state="collapsed")
    set_background('./bgs/654.jpg')
    check_auth()
    
    st.title("Cervical Cancer Screening Tool")
    st.write(f"User: {st.session_state.username}")
    st.write(f"Facility: {st.session_state.facility}")

    # Initialize Supabase client
    supabase = init_supabase()

    #device handling
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # page setup
    st.markdown("<h1 style='text-align: center; color: #A5FFFD; border: 2px solid #30B0C2; border-radius: 10px; padding: 10px;'>Cervical Cancer Screening Tool</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Please upload an image for analysis</h2>", unsafe_allow_html=True)


    # initial image and diagnosis data
    if 'image_data' not in st.session_state:
        st.session_state.image_data = None
    if 'raw_image' not in st.session_state:
        st.session_state.raw_image = None
    if 'diagnosis_data' not in st.session_state:
        st.session_state.diagnosis_data = None
    if 'facility' not in st.session_state:
        st.session_state.facility = None
    if 'client_code' not in st.session_state:
        st.session_state.client_code = None

    # upload file
    file = st.file_uploader(label='Upload image for screening', type=['jpeg', 'jpg', 'png'])

    try:
        # load classifier
        model = YOLO("./model/best.pt")
        model.to(device)  # Move model to appropriate device
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        st.stop()

    # display image and process
    if st.button("Screen"):
        if file is not None:
            image = Image.open(file).convert('RGB')
            st.image(image, use_column_width=False, width=400, caption='Uploaded Image')

            # classify image
            class_name, conf_score = classify(image, model)

            # store the data in session state
            st.session_state.image_data = image
            st.session_state.diagnosis_data = {
                'class_name': class_name,
                'conf_score': conf_score
            }

            # write classification
            st.subheader(f"Diagnosis: {class_name}")
            st.write(f"Confidence Score: {conf_score:.2%}")
            
            # Show escalate button if confidence is below 90%
            if conf_score < 0.9:
                st.warning("Confidence score is below 90%. Consider escalating to a clinician.")

    # Modify the escalation section:
    if (st.session_state.diagnosis_data is not None and 
        st.session_state.diagnosis_data['conf_score'] < 0.9):
        
        # Enter the client code
        client_code = st.text_input("Client_Code", placeholder="Please enter the client code")

        # store client code in session state
        st.session_state.client_code = client_code

    if (st.session_state.diagnosis_data is not None 
        and st.session_state.facility is not None 
        and st.session_state.client_code is not None 
        and st.session_state.diagnosis_data['conf_score'] < 0.9):
        if st.button("Escalate to Clinician", key="escalate_button"):
            with st.spinner("Sending to clinician..."):
                # Save image to Supabase storage
                image_url = save_image_to_supabase(supabase, file, st.session_state.client_code)
                
                # Save screening data to Supabase table
                save_screening_data(
                    supabase,
                    image_url,
                    st.session_state.diagnosis_data['class_name'],
                    st.session_state.diagnosis_data['conf_score'],
                    st.session_state.facility,
                    st.session_state.client_code
                )
                
                if send_to_clinician(
                    st.session_state.image_data, 
                    st.session_state.diagnosis_data['class_name'],
                    st.session_state.diagnosis_data['conf_score'],
                    st.session_state.selected_facility,
                    client_code
                ):
                    st.success("Successfully sent to clinician for review!")
                    # Reset session state after successful escalation
                    st.session_state.image_data = None
                    st.session_state.diagnosis_data = None
                    st.session_state.client_code = None
                else:
                    st.error("Failed to send to clinician. Please try again or contact support.")

if __name__ == "__main__":
    screening_page()