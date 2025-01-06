import streamlit as st
from streamlit_navigation_bar import st_navbar
from src.utils.utility_functions import set_page_config

set_page_config()

#page = st_navbar(["Pre-survey", "Admin Data Quality", "Post-survey"])

if __name__ == "__main__":
     st.markdown("<h1 style='text-align: center;'>CEGIS Discsim Project", unsafe_allow_html=True)
