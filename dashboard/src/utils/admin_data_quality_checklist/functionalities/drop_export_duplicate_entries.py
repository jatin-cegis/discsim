import json
import os
import sys
from src.utils.admin_data_quality_checklist.helpers.graph_functions import plot_pie_chart
import streamlit as st
import pandas as pd
import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE_URL = os.getenv("API_BASE_URL")

DROP_EXPORT_DUPLICATES_ENDPOINT = f"{API_BASE_URL}/drop_export_duplicates"
GET_PROCESSED_DATA_ENDPOINT = f"{API_BASE_URL}/get_processed_data"
GET_DATAFRAME_ENDPOINT = f"{API_BASE_URL}/get_dataframe"

def drop_export_duplicate_entries(uploaded_file, df):
    st.subheader("Drop/Export Duplicate Entries")
    st.write("The function identifies duplicate entries in the dataset and returns the unique and the duplicate DataFrames individually.")
    with st.expander("ℹ️ Info"):
        st.markdown("""
        - Removes duplicate rows based on specified unique identifier column(s).
        - Options:
        - Select which duplicate to keep: first, last, or none.
        - Export duplicates to a separate file.
        - Supports processing large files in chunks for better performance.
        - Handles infinity and NaN values by replacing them with NaN.
        - Valid input format: CSV file
        """)
    uid_col = st.multiselect("Select unique identifier column(s)", df.columns.tolist())
    kept_row = st.selectbox("Which duplicate to keep: first(keeps the first occurrence), last(keeps the last occurrence), or none(removes all occurrences)", ["first", "last", "none"])
    export = st.checkbox("Export duplicates", value=True)
    chunksize = st.number_input("Chunksize (optional, leave 0 for no chunking): Use only for very large datasets, set to 10000 to start with", min_value=0, step=1000)

    if st.button("Process Duplicates"):
        with st.spinner("Processing..."):
            try:
                uploaded_file.seek(0)
                files = {"file": ("uploaded_file.csv", uploaded_file, "text/csv")}
                payload = {
                    "uidCol": uid_col,
                    "keptRow": kept_row,
                    "export": export,
                    "chunksize": chunksize if chunksize > 0 else None
                }
                input_data = json.dumps(payload)
                response = requests.post(
                    DROP_EXPORT_DUPLICATES_ENDPOINT,
                    files=files,
                    data={"input_data": input_data}
                )

                if response.status_code == 200:
                    result = response.json()
                    st.success("Processing completed!")
                    st.session_state.drop_export_complete = True

                    unique_df = pd.DataFrame(requests.get(f"{GET_DATAFRAME_ENDPOINT}?data_type=unique").json())
                    duplicate_df = pd.DataFrame(requests.get(f"{GET_DATAFRAME_ENDPOINT}?data_type=duplicate").json())
                    # Visualize the results
                    total_rows = len(unique_df) + len(duplicate_df)
                    unique_rows = len(unique_df)
                    duplicate_rows = len(duplicate_df)

                    fig = plot_pie_chart([f"Unique Rows ({unique_rows})", f"Duplicate Rows ({duplicate_rows})"], [unique_rows, duplicate_rows], "Dataset Composition")
                    st.plotly_chart(fig)
                    # Display dataframes
                    st.subheader("Unique Rows")
                    try:
                        unique_df = pd.DataFrame(requests.get(f"{GET_DATAFRAME_ENDPOINT}?data_type=unique").json())
                        st.dataframe(unique_df)
                    except Exception as e:
                        st.error(f"Error displaying unique rows: {str(e)}")

                    if export:
                        st.subheader("Duplicate Rows")
                        try:
                            duplicate_df = pd.DataFrame(requests.get(f"{GET_DATAFRAME_ENDPOINT}?data_type=duplicate").json())
                            st.dataframe(duplicate_df)
                        except Exception as e:
                            st.error(f"Error displaying duplicate rows: {str(e)}")
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    if st.session_state.get('drop_export_complete', False):
        # Download Unique Rows
        unique_filename = st.text_input("Enter filename for unique rows (without .csv)", value="unique_rows")
        if st.button("Download Unique Rows"):
            download_url = f"{GET_PROCESSED_DATA_ENDPOINT}?data_type=unique&filename={unique_filename}.csv"
            st.markdown(f'<a href="{download_url}" download="{unique_filename}.csv">Click here to download unique rows</a>', unsafe_allow_html=True)
            st.warning("Please consider uploading the newly downloaded deduplicated file for further analysis.")
        
        # Download Duplicate Rows (if exported)
        if export:
            duplicate_filename = st.text_input("Enter filename for duplicate rows (without .csv)", value="duplicate_rows")
            if st.button("Download Duplicate Rows"):
                download_url = f"{GET_PROCESSED_DATA_ENDPOINT}?data_type=duplicate&filename={duplicate_filename}.csv"
                st.markdown(f'<a href="{download_url}" download="{duplicate_filename}.csv">Click here to download duplicate rows</a>', unsafe_allow_html=True)
                st.warning("Note that this is the CSV containing all the duplicate entries, download the unique deduplicated file for better analysis.")
    else:
        # Reset the download options
        st.session_state.unique_filename = ""
        st.session_state.duplicate_filename = ""