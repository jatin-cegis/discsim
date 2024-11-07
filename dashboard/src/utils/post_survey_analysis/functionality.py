import streamlit as st
import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
POST_SURVEY_ANALYSIS_ENDPOINT = f"{API_BASE_URL}/post_survey_analysis"

def execute_post_survey_analysis(uploaded_file, df):
    st.header("Composite Discrepancy Score Calculation")

    # Display the dataframe
    st.subheader("Uploaded Data")
    st.write(df.head())

    # Check if necessary columns are present
    required_columns = ['child', 'L0_height', 'L1_height', 'L0_weight', 'L1_weight']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        st.error(f"The following required columns are missing: {', '.join(missing_columns)}")
        return

    # Input for margin of error
    margin_of_error = st.number_input("Margin of Error", min_value=0.0, value=0.0, step=0.1,
                                      help="Acceptable margin of error to account for natural growth or measurement errors.")

    # Prepare data for API
    uploaded_file.seek(0)
    files = {"file": ("uploaded_file.csv", uploaded_file, "text/csv")}
    data = {"margin_of_error": margin_of_error}

    # Send request to API
    with st.spinner("Calculating discrepancy scores..."):
        response = requests.post(POST_SURVEY_ANALYSIS_ENDPOINT, files=files, data=data)

    if response.status_code == 200:
        result = response.json()
        # Display results
        st.subheader("Discrepancy Measures")
        st.write("**Average Discrepancy in Height and Weight:**")
        st.write(pd.DataFrame(result['discrepancy_measures'], index=[0]))

        st.subheader("Discrepancy Prevalence")
        st.write(pd.DataFrame(result['discrepancy_prevalence'], index=[0]))

        st.subheader("Composite Discrepancy Score")
        st.metric(label="Composite Discrepancy Score", value=round(result['composite_discrepancy_score'], 2))

    else:
        st.error(f"Error in calculation: {response.text}")
