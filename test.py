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

from utils.tools import classify, set_background

load_dotenv()

def save_image_temporarily(image):
    """Save the PIL image temporarily and return the path"""
    temp_path = "temp_image.jpg"
    image.save(temp_path)
    return temp_path

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
    
    temp_path = save_image_temporarily(image)

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

#device handling
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# page setup
st.set_page_config(page_title='Cervical Cancer Screening Tool', layout='wide')
st.markdown("<h1 style='text-align: center; color: #A5FFFD; border: 2px solid #30B0C2; border-radius: 10px; padding: 10px;'>Cervical Cancer Screening Tool</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Please upload an image for analysis</h2>", unsafe_allow_html=True)

set_background('./bgs/bg4.jpg')

# get list of facilities
FACILITIES = os.getenv('FACILITIES')

# initial image and diagnosis data
if 'image_data' not in st.session_state:
    st.session_state.image_data = None
if 'diagnosis_data' not in st.session_state:
    st.session_state.diagnosis_data = None
if 'selected_facility' not in st.session_state:
    st.session_state.selected_facility = None
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
    
    # Add facility selector dropdown
    selected_facility = st.selectbox(
        "Select Referring Facility",
        options=FACILITIES,
        index=None,
        placeholder="Choose facility..."
    )
    
    # Store selected facility in session state
    st.session_state.selected_facility = selected_facility
    
    # Enter the client code
    client_code = st.text_input("Client_Code", placeholder="Please enter the client code")

    # store client code in session state
    st.session_state.client_code = client_code



if (st.session_state.diagnosis_data is not None 
    and st.session_state.selected_facility is not None 
    and st.session_state.client_code is not None 
    and st.session_state.diagnosis_data['conf_score'] < 0.9):
    if st.button("Escalate to Clinician", key="escalate_button"):
        with st.spinner("Sending to clinician..."):
            if send_to_clinician(
                st.session_state.image_data, 
                st.session_state.diagnosis_data['class_name'],
                st.session_state.diagnosis_data['conf_score'],
                selected_facility,
                client_code
            ):
                st.success("Successfully sent to clinician for review!")
                 # Reset session state after successful escalation
                st.session_state.image_data = None
                st.session_state.diagnosis_data = None
                st.session_state.selected_facility = None
                st.session_state.client_code = None
            else:
                st.error("Failed to send to clinician. Please try again or contact support.")