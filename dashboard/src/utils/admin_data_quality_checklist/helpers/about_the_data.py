import streamlit as st
from src.utils.admin_data_quality_checklist.helpers.preliminary_tests import run_preliminary_tests

def abouthepage(file):
    st.header("About the Data")
    run_preliminary_tests(file)