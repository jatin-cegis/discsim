import json
import os
from src.utils.admin_data_quality_checklist.helpers.graph_functions import plot_pie_chart
import streamlit as st
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")

DROP_EXPORT_DUPLICATE_ROWS_ENDPOINT = f"{API_BASE_URL}/drop_export_duplicate_rows"
GET_PROCESSED_DATA_ENDPOINT = f"{API_BASE_URL}/get_processed_data"
GET_DATAFRAME_ENDPOINT = f"{API_BASE_URL}/get_dataframe"

def drop_export_duplicate_rows(uploaded_file):
    customcss = """
        <style>
        div[data-testid="stExpander"] summary{
            padding:0.4rem 1rem;
        }
        .stHorizontalBlock{
            //margin-top:-30px;
        }
        .st-key-processBtn button{
            background-color:#3b8e51;
            color:#fff;
            border:none;
        }
        .st-key-processBtn button:hover,.st-key-processBtn button:active,.st-key-processBtn button:focus,st-key-processBtn button:focus:not(:active){
            color:#fff!important;
            border:none;
        }
        </style>
    """
    st.markdown(customcss, unsafe_allow_html=True)
    st.session_state.drop_export_entries_complete = False
    title_info_markdown = """
        This function checks for fully duplicate rows in the dataset and returns the unique and the duplicate DataFrames individually.
        - Analyzes the dataset to find completely duplicated rows.
        - Removes duplicate rows based on all columns.
        - Options:
        - Select which duplicate to keep: first, last, or none.
        - Export duplicates to a separate file.
        - Provides the count and percentage of duplicate rows in the dataset.
        - Valid input format: CSV file
    """
    st.markdown("<h2 style='text-align: center;font-weight:800;color:#136a9a;margin-top:-15px;'>Inspect Duplicate Rows</h2>", unsafe_allow_html=True, help=title_info_markdown)
    st.markdown("<p style='color:#3b8e51;margin-bottom:20px'>The function helps you to inspect if any duplicate exist in the dataset. You can get a modified dataset with unique rows only</p>", unsafe_allow_html=True)

    kept_row = st.selectbox("Which duplicate to keep", ["first", "last", "none"], help="first(keeps the first occurrence), last(keeps the last occurrence), or none(removes all occurrences)")

    if st.button("Check for duplicate rows",key="processBtn"):
        with st.spinner("Processing..."):
            try:
                uploaded_file.seek(0)
                files = {"file": ("uploaded_file.csv", uploaded_file, "text/csv")}
                payload = {
                    "keptRow": kept_row,
                }
                input_data = json.dumps(payload)
                response = requests.post(
                    DROP_EXPORT_DUPLICATE_ROWS_ENDPOINT,
                    files=files,
                    data={"input_data": input_data}
                )

                if response.status_code == 200:
                    result = response.json()
                    st.session_state.drop_export_rows_complete = True

                    unique_df = pd.DataFrame(requests.get(f"{GET_DATAFRAME_ENDPOINT}?data_type=unique").json())
                    duplicate_df = pd.DataFrame(requests.get(f"{GET_DATAFRAME_ENDPOINT}?data_type=duplicate").json())
                    
                    # Visualize the results
                    unique_rows = len(unique_df)
                    duplicate_rows = len(duplicate_df)

                    fig = plot_pie_chart([f"Unique Rows ({unique_rows})", f"Duplicate Rows ({duplicate_rows})"], [unique_rows, duplicate_rows], "Dataset Composition")
                    st.plotly_chart(fig)
                    
                    # Display dataframes
                    st.subheader("Unique Rows")
                    with st.expander("Unique Rows:"):
                        st.dataframe(unique_df, hide_index=True)

                    if len(duplicate_df)>0:
                        st.subheader("Duplicate Rows")
                        with st.expander("Duplicate Rows:"):
                            st.dataframe(duplicate_df, hide_index=True)
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")