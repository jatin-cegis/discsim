import json
import os
from src.utils.admin_data_quality_checklist.helpers.graph_functions import plot_pie_chart
import streamlit as st
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")

DROP_EXPORT_DUPLICATES_ENDPOINT = f"{API_BASE_URL}/drop_export_duplicates"
GET_PROCESSED_DATA_ENDPOINT = f"{API_BASE_URL}/get_processed_data"
GET_DATAFRAME_ENDPOINT = f"{API_BASE_URL}/get_dataframe"

def drop_export_duplicate_entries(uploaded_file, df):
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
        .st-key-uidCol label p::after,.st-key-duplicateKeep label p::after { 
            content: " *";
            color: red;
        }
        </style>
    """
    st.markdown(customcss, unsafe_allow_html=True)

    st.session_state.drop_export_rows_complete = False
    title_info_markdown = """
        The function identifies duplicate entries in the dataset and returns the unique and the duplicate DataFrames individually.
        - Removes duplicate rows based on specified unique identifier column(s).
        - Options:
        - Select which duplicate to keep: first, last, or none.
        - Export duplicates to a separate file.
        - Supports processing large files in chunks for better performance.
        - Handles infinity and NaN values by replacing them with NaN.
        - Valid input format: CSV file
    """
    st.markdown("<h2 style='text-align: center;font-weight:800;color:#136a9a;margin-top:-15px'>Inspect Duplicate Entries</h2>", unsafe_allow_html=True, help=title_info_markdown)
    st.markdown("<p style='color:#3b8e51;margin-bottom:20px'>The function helps you to inspect if any duplicate entries are present in the unique identifier column(s) you selected. You can get a modified dataset with unique entries only</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        uid_col = st.multiselect("Select unique identifier column(s) [up to 4 columns allowed]", df.columns.tolist(),key="uidCol")
    with col2: 
        helpKeep = """
            1. First occurrence (in case duplicate, i.e. >1, entries exist, keeps the first occurrence and drops the rest)
            2. Last occurrence (in case duplicate, i.e. >1, entries exist, keeps the last occurrence and drops the rest)
            3. Drop all occurrences (in case duplicate, i.e. >1, entries exist, drops every occurrence
        """
        kept_row = st.selectbox("Which duplicate(s) to keep?", ["first", "last", "none"], help=helpKeep ,key="duplicateKeep")
    with col3:
        chunksize = st.number_input("Chunksize (optional, select 0 for no chunking)", min_value=0, step=1000, help="Use only for very large datasets, set to 10000 to start with")

    if st.button("Check for duplicate entries",key="processBtn"):
        with st.spinner("Processing..."):
            try:
                uploaded_file.seek(0)
                files = {"file": ("uploaded_file.csv", uploaded_file, "text/csv")}
                payload = {
                    "uidCol": uid_col,
                    "keptRow": kept_row,
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
                    st.session_state.drop_export_entries_complete = True

                    unique_df = pd.DataFrame(requests.get(f"{GET_DATAFRAME_ENDPOINT}?data_type=unique").json())
                    duplicate_df = pd.DataFrame(requests.get(f"{GET_DATAFRAME_ENDPOINT}?data_type=duplicate").json())
                    # Visualize the results
                    unique_rows = len(unique_df)
                    duplicate_rows = len(duplicate_df)

                    fig = plot_pie_chart([f"Unique Entries ({unique_rows})", f"Duplicate Entries ({duplicate_rows})"], [unique_rows, duplicate_rows], "Dataset Composition")
                    st.plotly_chart(fig)
                    col5,col4 = st.columns(2)
                    # Display dataframes

                    col5.subheader("Unique Entries")
                    col5.text("In case you want to continue your analysis using the modified dataset, you can view and download the modified dataset with only unique entries here")
                    with col5.expander("Show/export unique entries"):
                        try:
                            unique_df = pd.DataFrame(requests.get(f"{GET_DATAFRAME_ENDPOINT}?data_type=unique").json())
                            unique_df.index.name = 'SN'
                            unique_df.index = unique_df.index + 1
                            st.dataframe(unique_df, hide_index=True)
                        except Exception as e:
                            st.error(f"Error displaying unique rows: {str(e)}")

                    col4.subheader("Duplicate Entries")
                    col4.text("In case you want to use them later for your reference, you can view or download the duplicate rows dropped from the original dataset here")
                    duplicate_df = pd.DataFrame(requests.get(f"{GET_DATAFRAME_ENDPOINT}?data_type=duplicate").json())
                    if len(duplicate_df)>0:
                        with col4.expander("Show/export duplicate entries"):
                            try:
                                duplicate_df.index.name = 'SN'
                                duplicate_df.index = duplicate_df.index + 1
                                st.dataframe(duplicate_df, hide_index=False)
                            except Exception as e:
                                st.error(f"Error displaying duplicate rows: {str(e)}")
                    else:
                        col4.warning("No Duplicate Entries")

                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        