import streamlit as st
from streamlit_navigation_bar import st_navbar
from src.utils.pre_survey_analysis.third_party_sampling_strategy import third_party_sampling_strategy
from src.utils.utility_functions import set_page_config

set_page_config()

def pre_survey_analysis():
    title_info_markdown = '''
        Welcome to the Pre-survey Analysis module. This module helps you determine optimal sample sizes and sampling strategies for your survey. Choose from the following options:
        
        1. L1 Sample Size Calculator: Estimate the supervisor sample size required to guarantee identification of outlier subordinates.
        2. L2 Sample Size Calculator: Calculate the optimal sample size for measuring discrepancy at different administrative levels.
        3. Third-Party Sampling Strategy Predictor: Determine the best strategy for third-party sampling given resource constraints.
        
        Select an option from the sidebar to get started.
    '''
    st.sidebar.header("Pre-survey Analysis Options")

    # Second level dropdown for Pre-survey Analysis
    pre_survey_option = st.sidebar.selectbox("Select Pre-survey Analysis", ["Third-Party Sampling Strategy Predictor"], help=title_info_markdown)
            
    if pre_survey_option == "Third-Party Sampling Strategy Predictor":
        third_party_sampling_strategy()


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
    page = st_navbar(["Pre Survey", "Admin Data Quality", "Post Survey"],styles=navStyles,options=navOptions)
    if page == "Admin Data Quality":
          st.switch_page("pages/2_Admin_Data_Quality_Checklist.py")
    if page == "Post Survey":
          st.switch_page("pages/3_Post_Survey.py")
    pre_survey_analysis()