import streamlit as st
from PIL import Image
import sys
import os

from src.functions.pre_survey_analysis import pre_survey_analysis
from src.functions.admin_data_quality_checklist import admin_data_quality_check

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to logo.png
logo_path = os.path.join(script_dir, "logo.jpg")
im = Image.open(logo_path)

st.set_page_config(
        page_title="DiscSim | CEGIS",
        layout="wide",
        page_icon=im,
    )

def main():
    st.sidebar.title("DiscSim Modules")
    
    # First level dropdown
    main_option = st.sidebar.selectbox("Select Module", ["Pre-survey Analysis", "Administrative Data Quality"])
    
    if main_option == "Pre-survey Analysis":
        pre_survey_analysis()
    elif main_option == "Administrative Data Quality":
        admin_data_quality_check()

if __name__ == "__main__":
    main()
