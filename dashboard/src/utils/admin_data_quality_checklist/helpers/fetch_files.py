import streamlit as st
import requests
import os
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")

GET_FILE_ENDPOINT = f"{API_BASE_URL}/get_file"

def fetch_file_from_api(file_id):
    file_response = requests.get(f"{GET_FILE_ENDPOINT}/{file_id}")
    if file_response.status_code == 200:
        file_data = file_response.json()
        file_content = file_data["content"].encode('utf-8')
        uploaded_file = BytesIO(file_content)
        uploaded_file.name = file_data["filename"]
        return uploaded_file
    else:
        st.error(f"Failed to fetch file with ID {file_id}.")
        return None