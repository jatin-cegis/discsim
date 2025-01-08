import streamlit as st
from src.utils.utility_functions import set_page_config,setheader,setFooter
set_page_config()



if __name__ == "__main__":
    st.markdown("<h1 style='text-align: center;'>CEGIS Discsim Project", unsafe_allow_html=True)
    selectedNav = setheader("Pre Survey")
    if selectedNav == "Pre Survey":
          st.switch_page("pages/1_Pre_Survey.py")
    if selectedNav == "Admin Data Quality":
          st.switch_page("pages/2_Admin_Data_Quality_Checklist.py")
    if selectedNav == "Post Survey":
          st.switch_page("pages/3_Post_Survey.py")
    setFooter()