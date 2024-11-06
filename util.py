import base64
import streamlit as st
from PIL import ImageOps, Image



def set_background(image_file):
    with open(image_file, "rb") as f:
        img_data = f.read()
    b64_encoded = base64.b64encode(img_data).decode()
    style = f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{b64_encoded});
            background-size: cover;
        }}
        </style>
    """
    st.markdown(style, unsafe_allow_html=True)


def classify(image, model):
    # make prediction
    prediction = model.predict(image, save=True, show_labels=True, imgsz=640, conf=0.8)
    result = prediction[0]

    # get class name
    pred_class_idx = result.probs.top1
    pred_class_name = model.names[pred_class_idx]

    # get confidence score
    confidence_score = result.probs.top1conf.item()

    return pred_class_name, confidence_score
