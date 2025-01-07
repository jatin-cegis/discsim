import streamlit as st
from streamlit_navigation_bar import st_navbar
from src.utils.utility_functions import set_page_config
set_page_config()



if __name__ == "__main__":
     st.markdown("<h1 style='text-align: center;'>CEGIS Discsim Project", unsafe_allow_html=True)
     navStyles = {
        "nav": {
            "background-color": "#fff5e6",
            "justify-content": "right",
        },
        "div": {
            "max-width": "30rem",
        },
        "span": {
            "color": "#006897",
            "font-weight": "700",
        },
        "active": {
            "color": "#D3A518",
            "font-weight": "800",
        }
     }
     navOptions = {
        "fix_shadow":False
     }
     page = st_navbar(["Pre Survey", "Admin Data Quality", "Post Survey"],selected="Pre Survey",styles=navStyles,options=navOptions)
     if page == "Pre Survey":
          st.switch_page("pages/1_Pre_Survey.py")
     if page == "Admin Data Quality":
          st.switch_page("pages/2_Admin_Data_Quality_Checklist.py")
     if page == "Post Survey":
          st.switch_page("pages/3_Post_Survey.py")