import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import logging

logger = logging.getLogger(__name__)

def send_to_clinician(image, class_name, conf_score, selected_facility, client_code):
    """Send image and details to clinician via email"""
    subject = "Diagnosis Escalation"
    body = f"URGENT REVIEW NEEDED\nFacility: {selected_facility}\nClient Code: {client_code}\nDiagnosis: {class_name}\nConfidence Score: {conf_score:.2%}\nPlease review the attached image."
    
    sender_email = os.getenv('SENDER_EMAIL')
    recipient_email = os.getenv('RECIPIENT_EMAIL')
    sender_password = os.getenv('GOOGLE_APP_PASSWORD')

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    
    temp_path = "temp_image.jpg"
    image.save(temp_path)

    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = recipient_email

    body_part = MIMEText(body)
    message.attach(body_part)

    with open(temp_path, 'rb') as file:
        attachment = MIMEApplication(file.read(), Name="Image.jpg")
        attachment['Content-Disposition'] = 'attachment; filename="Image.jpg"'
        message.attach(attachment)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        success = True
    except Exception as e:
        success = False
        logger.error(f"Error sending to clinician: {e}", exc_info=True)
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return success