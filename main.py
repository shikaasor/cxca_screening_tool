import streamlit as st
from ultralytics import YOLO
from PIL import Image
import pywhatkit
from datetime import datetime
import pytz
from io import BytesIO
import os
import torch

from util import classify, set_background

def save_image_temporarily(image):
    """Save the PIL image temporarily and return the path"""
    temp_path = "temp_image.jpg"
    image.save(temp_path)
    return temp_path

def send_to_clinician(image, class_name, conf_score):
    """Send image and details to clinician via WhatsApp"""
    # Replace with actual clinician's phone number (including country code)
    CLINICIAN_PHONE = "+1234567890"  
    
    # Save image temporarily
    temp_path = save_image_temporarily(image)
    
    # Get current time (add 2 minutes to allow for WhatsApp Web to process)
    now = datetime.now(pytz.timezone('UTC'))
    send_time = now.hour
    send_minute = now.minute + 2
    
    # Prepare message
    


    message = f"URGENT REVIEW NEEDED\nDiagnosis: {class_name}\nConfidence Score: {conf_score:.2%}\nPlease review the attached image."
    
    try:
        # Send message and image via WhatsApp
        pywhatkit.sendwhats_image(
            receiver='phone_no',
            img_path=temp_path,
            caption=message,
            wait_time=15,
            tab_close=False
        )
        success = True
    except Exception as e:
        success = False
        st.error(f"Error sending to clinician: {str(e)}")
    
    # Clean up temporary file
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return success

#device handling
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# page setup
st.set_page_config(page_title='Cervical Cancer Screening Tool', layout='wide')
st.markdown("<h1 style='text-align: center; color: #A5FFFD; border: 2px solid #30B0C2; border-radius: 10px; padding: 10px;'>Cervical Cancer Screening Tool</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Please upload an image for analysis</h2>", unsafe_allow_html=True)

set_background('./bgs/bg4.jpg')

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

        # write classification
        st.subheader(f"Diagnosis: {class_name}")
        st.write(f"Confidence Score: {conf_score:.2%}")
        
        # Show escalate button if confidence is below 90%
        if conf_score < 0.9:
            st.warning("Confidence score is below 90%. Consider escalating to a clinician.")
            if st.button("Escalate to Clinician"):
                with st.spinner("Sending to clinician..."):
                    if send_to_clinician(image, class_name, conf_score):
                        st.success("Successfully sent to clinician for review!")
                    else:
                        st.error("Failed to send to clinician. Please try again or contact support.")