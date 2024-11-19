import streamlit as st
from src.utils.pre_survey_analysis.third_party_sampling_strategy import third_party_sampling_strategy

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