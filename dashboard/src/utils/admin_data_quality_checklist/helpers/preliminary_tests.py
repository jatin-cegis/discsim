import streamlit as st
import requests
import sys
import os
from dotenv import load_dotenv
from src.utils.admin_data_quality_checklist.helpers.functionality_map import get_relevant_functionality

load_dotenv()

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE_URL = os.getenv("API_BASE_URL")

PRELIMINARY_TESTS_ENDPOINT = f"{API_BASE_URL}/preliminary_tests"

def run_preliminary_tests(uploaded_file):
    with st.spinner("Running preliminary tests on the uploaded file..."):
        try:
            uploaded_file.seek(0)  # Reset file pointer before reading again
            files = {"file": ("uploaded_file.csv", uploaded_file, "text/csv")}
            response = requests.post(PRELIMINARY_TESTS_ENDPOINT, files=files)
            
            if response.status_code == 200:
                result = response.json()
                if result["status"] == 0:
                    if result["warnings"]:
                        st.warning("Warnings:")
                        for warning in result["warnings"]:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"- {warning}")
                            with col2:
                                relevant_func = get_relevant_functionality(warning)
                                if st.button(f"Check {relevant_func}", key=f"warning_button_{warning}"):
                                    st.session_state.navbar_selection = relevant_func
                    return True
                else:
                    st.error("Preliminary tests failed. Please check your file and try again.")
                    return False
            else:
                st.error(f"Error in preliminary tests: {response.status_code}")
                return False
        except Exception as e:
            st.error(f"Error during preliminary tests: {str(e)}")
            return False
