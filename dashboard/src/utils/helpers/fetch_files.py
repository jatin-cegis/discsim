import streamlit as st
import requests
import os
import io
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
@st.cache_data(ttl=300)
def fetch_file_from_api(file_id):
    get_file_endpoint = f"{API_BASE_URL}/get_file/{file_id}"
    response = requests.get(get_file_endpoint)
    if response.status_code == 200:
        try:
            file_data = response.json()
        except ValueError:
            raise Exception(f"Invalid response format: {response.text}")
        if "content" in file_data and "filename" in file_data:
            file_content = file_data["content"]
            uploaded_file = io.StringIO(file_content)
            uploaded_file.name = file_data["filename"]
            return uploaded_file
        else:
            raise Exception("Invalid file data received from API.")
    else:
        raise Exception(f"Failed to fetch file from API: {response.text}")
