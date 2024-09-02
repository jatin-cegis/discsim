import json
import os
import sys
import traceback
import streamlit as st
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE_URL = os.getenv("API_BASE_URL")

FREQUENCY_TABLE_ENDPOINT = f"{API_BASE_URL}/frequency_table"

def frequency_table_analysis(uploaded_file, df):
    st.subheader("Frequency Table Analysis")
    st.write(
        "This function takes a variable as a user input and returns the frequency table of number and share of observations of each unique value present in the variable."
    )
    with st.expander("ℹ️ Info"):
        st.markdown(
            """
            - Generates a frequency table for a specified column in the dataset.
            - Options:
            - Select a column to analyze
            - Specify the number of top frequent values to display separately
            - Optionally group by a categorical variable
            - Optionally filter by a categorical variable
            - Provides counts and percentages for each unique value in the selected column.
            - Valid input format: CSV file
            """
        )

    column_to_analyze = st.selectbox("Select column to analyze", df.columns.tolist())
    top_n = st.number_input(
        "Number of top frequent values to display(0 for all values)", min_value=0, value=0
    )
    group_by = st.selectbox("Group by (optional): Analyze missing entries within distinct categories of another column. This is useful if you want to understand how missing values are distributed across different groups.", ["None"] + df.columns.tolist())
    filter_by_col = st.selectbox("Filter by (optional): Focus on a specific subset of your data by selecting a specific value in another column. This is helpful when you want to analyze missing entries for a specific condition.", ["None"] + df.columns.tolist())

    if filter_by_col != "None":
        filter_by_value = st.selectbox("Filter value", df[filter_by_col].unique().tolist())

    if st.button("Generate Frequency Table"):
        with st.spinner("Generating frequency table..."):
            try:
                uploaded_file.seek(0)  # Reset file pointer
                files = {"file": ("uploaded_file.csv", uploaded_file, "text/csv")}
                payload = {
                    "column_to_analyze": column_to_analyze,
                    "top_n": top_n,
                    "group_by": group_by if group_by != "None" else None,
                    "filter_by": {filter_by_col: filter_by_value} if filter_by_col != "None" else None,
                }
                response = requests.post(FREQUENCY_TABLE_ENDPOINT, files=files, data={"input_data": json.dumps(payload)})

                if response.status_code == 200:
                    result = response.json()
                    st.success("Frequency table generated!")

                    if result["grouped"]:
                        st.write("Combined Frequency Table for All Groups:")
                        full_table, top_n_table = result["analysis"]

                        # Determine if all values should be shown
                        show_all_values = top_n <= 0 or top_n >= len(full_table)

                        if not show_all_values:
                            st.write(f"Top {top_n} frequent values:")
                            top_n_df = pd.DataFrame(top_n_table)
                            top_n_df = top_n_df.sort_values("count", ascending=False)
                            top_n_df = top_n_df[[column_to_analyze, group_by, "count", "share %"]]
                            st.dataframe(top_n_df, use_container_width=True, hide_index=True)
                        else:
                            st.write("All Frequency Values:")
                            full_df = pd.DataFrame(full_table)
                            full_df = full_df[[column_to_analyze, group_by, "count", "share %"]]
                            full_df = full_df.sort_values("count", ascending=False)
                            st.dataframe(full_df, use_container_width=True, hide_index=True)

                    else:
                        full_table, top_n_table = result["analysis"]
                        if top_n > 0:
                            st.write(f"Top {top_n} frequent values:")
                            top_n_df = pd.DataFrame(top_n_table)
                            top_n_df = top_n_df.sort_values("count", ascending=False)
                            top_n_df.columns = [column_to_analyze, "count", "share %"]
                            st.dataframe(top_n_df, use_container_width=True, hide_index=True)
                        else:
                            full_df = pd.DataFrame(full_table)
                            full_df.columns = [column_to_analyze, "count", "share %"]
                            full_df = full_df.sort_values("count", ascending=False)
                            st.dataframe(full_df, use_container_width=True, hide_index=True)

                    if result["filtered"]:
                        st.info(f"Results are filtered by {filter_by_col} = {filter_by_value}")
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.write("Traceback:", traceback.format_exc())
