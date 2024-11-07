import streamlit as st
from PIL import Image
import sys
import os
import pages as pg
from streamlit_navigation_bar import st_navbar
from dotenv import load_dotenv

load_dotenv()

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to logo.png
logo_path = os.path.join(script_dir, "logo.jpg")
logo_page_path = os.path.join(script_dir, "logo_page.png")
im_page = Image.open(logo_page_path)
im = Image.open(logo_path)

st.logo(im_page)

st.set_page_config(
        page_title="DiscSim | CEGIS",
        layout="wide",
        page_icon=im,
    )

page = st_navbar(["Pre-survey", "Admin Data Quality", "Post-survey"])

def main():
    
    if page == "Pre-survey":
        pg.pre_survey_analysis()
    elif page == "Admin Data Quality":
        pg.admin_data_quality_check()
    elif page == "Post-survey":
        pg.post_survey_analysis()

if __name__ == "__main__":
    main()
