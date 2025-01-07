import streamlit as st
import pandas as pd
from src.utils.state_management import initialize_states, reset_session_states, reset_upload
from src.utils.admin_data_quality_checklist.helpers.file_upload import handle_file_upload
from src.utils.admin_data_quality_checklist.helpers.preliminary_tests import run_preliminary_tests
from src.utils.admin_data_quality_checklist.helpers.functionality_map import execute_functionality, sidebar_functionality_select
from src.utils.utility_functions import set_page_config
from streamlit_navigation_bar import st_navbar

set_page_config()

def admin_data_quality_check():
    # File selection
    file_option = st.sidebar.radio("Choose an option:", ("Upload a new file", "Select a previously uploaded file"))

    # Initialize states
    initialize_states()

    # Clear relevant session state when switching options
    if st.session_state.previous_file_option != file_option:
        st.session_state.uploaded_file = None
        st.session_state.uploaded_file_id = None
        reset_session_states()
        st.session_state.previous_file_option = file_option

    uploaded_file = handle_file_upload(file_option, category="admin_data_quality_checklist")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.session_state.uploaded_file = uploaded_file
        if uploaded_file != st.session_state.previous_uploaded_file:
            reset_session_states()
            st.session_state.previous_uploaded_file = uploaded_file
            
        # Run preliminary tests
        if run_preliminary_tests(uploaded_file):
            
            # Sidebar for functionality selection
            functionality = sidebar_functionality_select()
            
            # Use the selected functionality
            st.session_state.navbar_selection = functionality
                        
            execute_functionality(functionality, uploaded_file, df)

    else:
        st.info("Please upload a CSV file to begin.")
        reset_session_states()
        st.session_state.previous_uploaded_file = None

if st.session_state.get('reset_upload', False):
    reset_upload()
    st.rerun()

if __name__ == "__main__":
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
    page = st_navbar(["Pre Survey", "Admin Data Quality", "Post Survey"],selected="Admin Data Quality",styles=navStyles,options=navOptions)
    if page == "Pre Survey":
          st.switch_page("pages/1_Pre_Survey.py")
    if page == "Post Survey":
          st.switch_page("pages/3_Post_Survey.py")
    admin_data_quality_check()