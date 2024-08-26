import streamlit as st
import pandas as pd
import sys
import os
from src.utils.state_management import initialize_states, reset_session_states, reset_upload
from src.utils.admin_data_quality_checklist.helpers.file_upload import handle_file_upload
from src.utils.admin_data_quality_checklist.helpers.display_preview import display_data_preview
from src.utils.admin_data_quality_checklist.helpers.preliminary_tests import run_preliminary_tests
from src.utils.admin_data_quality_checklist.helpers.select_function import sidebar_functionality_select
from src.utils.admin_data_quality_checklist.functionalities.unique_id_verifier import unique_id_verifier
from src.utils.admin_data_quality_checklist.functionalities.check_specific_columns_as_unique_id import check_specific_columns_as_unique_id
from src.utils.admin_data_quality_checklist.functionalities.drop_export_duplicate_entries import drop_export_duplicate_entries
from src.utils.admin_data_quality_checklist.functionalities.drop_export_duplicate_rows import drop_export_duplicate_rows
from src.utils.admin_data_quality_checklist.functionalities.missing_entries_analysis import missing_entries_analysis
from src.utils.admin_data_quality_checklist.functionalities.zero_entries_analysis import zero_entries_analysis
from src.utils.admin_data_quality_checklist.functionalities.indicator_fill_rate_analysis import indicator_fill_rate_analysis
from src.utils.admin_data_quality_checklist.functionalities.frequency_table_analysis import frequency_table_analysis

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def admin_data_quality_check():

    st.markdown("<h1 style='text-align: center;'>DiscSim Module 4: Administrative Data Quality Checks</h1>", unsafe_allow_html=True)

    # File selection
    file_option = st.radio("Choose an option:", ("Upload a new file", "Select a previously uploaded file"))

    # Initialize states
    initialize_states()

    # Clear relevant session state when switching options
    if st.session_state.previous_file_option != file_option:
        st.session_state.uploaded_file = None
        st.session_state.uploaded_file_id = None
        reset_session_states()
        st.session_state.previous_file_option = file_option

    uploaded_file = handle_file_upload(file_option)

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.session_state.uploaded_file = uploaded_file
        if uploaded_file != st.session_state.previous_uploaded_file:
            reset_session_states()
            st.session_state.previous_uploaded_file = uploaded_file
            
        # Run preliminary tests
        if run_preliminary_tests(uploaded_file):
            # Display data preview
            display_data_preview(uploaded_file)
            
            # Sidebar for functionality selection
            functionality = sidebar_functionality_select()
            
            # Use the selected functionality
            st.session_state.navbar_selection = functionality
                        
            if functionality == "Unique ID Verifier":
                unique_id_verifier(uploaded_file)

            elif functionality == "Check Specific Columns as Unique ID":
                check_specific_columns_as_unique_id(df)

            elif functionality == "Drop/Export Duplicate Entries":
                drop_export_duplicate_entries(uploaded_file, df)

            elif functionality == "Drop/Export Duplicate Rows":
                drop_export_duplicate_rows(uploaded_file)

            elif functionality == "Missing Entries Analysis":
                missing_entries_analysis(uploaded_file, df)

            elif functionality == "Zero Entries Analysis":
                zero_entries_analysis(uploaded_file, df)

            elif functionality == "Indicator Fill Rate Analysis":
                indicator_fill_rate_analysis(uploaded_file, df)

            elif functionality == "Frequency Table Analysis":
                frequency_table_analysis(uploaded_file, df)

    else:
        st.info("Please upload a CSV file to begin.")
        reset_session_states()
        st.session_state.previous_uploaded_file = None

    if st.session_state.get('reset_upload', False):
        reset_upload()
        st.rerun()