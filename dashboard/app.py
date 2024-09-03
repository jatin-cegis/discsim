import streamlit as st
from PIL import Image
import sys
import os
import pages as pg
from streamlit_navigation_bar import st_navbar

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

page = st_navbar(["Pre-survey Analysis", "Administrative Data Quality"])

def main():
    
    if page == "Pre-survey Analysis":
        pg.pre_survey_analysis()
    elif page == "Administrative Data Quality":
        pg.admin_data_quality_check()

if __name__ == "__main__":
    main()
