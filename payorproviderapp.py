import streamlit as st

import os
import io
import json
from openai import OpenAI
import tempfile

from pdf2image import convert_from_path
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

os.environ["OPENAI_API_KEY"] = (
    st.secrets["OPENAI_API_KEY"]
)

def perform_ocr(image_data):
    """Function to perform OCR"""
    endpoint = "https://healthcare-llm-ocr.cognitiveservices.azure.com/"
    key = st.secrets["Azure_OCR_key"]
    credential = AzureKeyCredential(key)
    document_analysis = DocumentAnalysisClient(endpoint=endpoint, credential=credential)
    poller = document_analysis.begin_analyze_document("prebuilt-layout", image_data)
    result = poller.result()
    return result

def extract_content(image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_byte_arr = img_byte_arr.getvalue()
    ocr_result = perform_ocr(img_byte_arr)
    return ocr_result.content

st.set_page_config(page_title= 'File Uploader')
df = st.file_uploader(label= 'Upload your dataset:')

def save_to_temp(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(uploaded_file.read())
        temp_path = temp_file.name
    return temp_path

if df: 
    pdf = save_to_temp(df)
    images = convert_from_path(pdf)  # List of PIL Images

    l = []
    for i in range(len(images)):
        l.append(extract_content(images[i]))

    client = OpenAI()

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that can respond in JSON format: {'response': '...'}",
        },
        {"role": "user", "content": f"Extarct only the  table data from the given text and covert it into JSON fromat {l}"},
    ]

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0,
        response_format={"type": "json_object"},
    )
    response = completion.choices[0].message.content
    response = json.loads(response)

    response