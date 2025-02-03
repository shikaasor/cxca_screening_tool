from supabase import create_client, Client
import os
from datetime import datetime
from PIL import Image

def init_supabase():
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    return create_client(supabase_url, supabase_key)

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