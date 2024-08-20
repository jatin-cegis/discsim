import json
import streamlit as st
import pandas as pd
import requests
from PIL import Image
import sys
import os
import numpy as np
import traceback
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to logo.png
logo_path = os.path.join(script_dir, "logo.jpg")
im = Image.open(logo_path)

st.set_page_config(
        page_title="DiscSim | CEGIS",
        layout="wide",
        page_icon=im,
    )

API_BASE_URL = "http://localhost:8000"

def admin_data_quality_check():
    def plot_pie_chart(labels, values, title):
        # Sort values and labels in descending order
        sorted_data = sorted(zip(values, labels), reverse=True)
        sorted_values, sorted_labels = zip(*sorted_data)
        fig = px.pie(names=sorted_labels, values=sorted_values, title=title)
        return fig

    def plot_100_stacked_bar_chart(data, x, y, color, title, x_label, y_label):
        fig = px.bar(data, x=x, y=y, color=color, title=title, 
                    labels={x: x_label, 'value': y_label},
                    barmode='relative')  # This makes it a 100% stacked bar chart
        
        fig.update_layout(legend_title_text='')
        return fig

    def get_relevant_functionality(warning):
        if "duplicate" in warning.lower():
            return "Drop/Export Duplicate Rows"
        elif "missing" in warning.lower():
            return "Missing Entries Analysis"
        elif "zero" in warning.lower():
            return "Zero Entries Analysis"
        else:
            return "Unique ID Verifier"

    # Define the API endpoints
    UPLOAD_FILE_ENDPOINT = f"{API_BASE_URL}/upload_file"
    GET_FILE_ENDPOINT = f"{API_BASE_URL}/get_file"
    PRELIMINARY_TESTS_ENDPOINT = f"{API_BASE_URL}/preliminary_tests"
    FIND_UNIQUE_IDS_ENDPOINT = f"{API_BASE_URL}/find_unique_ids"
    UNIQUE_ID_CHECK_ENDPOINT = f"{API_BASE_URL}/unique_id_check"
    DROP_EXPORT_DUPLICATES_ENDPOINT = f"{API_BASE_URL}/drop_export_duplicates"
    GET_PROCESSED_DATA_ENDPOINT = f"{API_BASE_URL}/get_processed_data"
    GET_DATAFRAME_ENDPOINT = f"{API_BASE_URL}/get_dataframe"
    DUPLICATE_ANALYSIS_ENDPOINT = f"{API_BASE_URL}/duplicate_analysis"
    REMOVE_DUPLICATES_ENDPOINT = f"{API_BASE_URL}/remove_duplicates"
    GET_DEDUPLICATED_DATA_ENDPOINT = f"{API_BASE_URL}/get_deduplicated_data"
    MISSING_ENTRIES_ENDPOINT = f"{API_BASE_URL}/missing_entries"
    ZERO_ENTRIES_ENDPOINT = f"{API_BASE_URL}/zero_entries"
    INDICATOR_FILL_RATE_ENDPOINT = f"{API_BASE_URL}/indicator_fill_rate"
    FREQUENCY_TABLE_ENDPOINT = f"{API_BASE_URL}/frequency_table"

    st.markdown("<h1 style='text-align: center;'>DiscSim Module 4: Administrative Data Quality Checks</h1>", unsafe_allow_html=True)

    # File selection
    file_option = st.radio("Choose an option:", ("Upload a new file", "Select a previously uploaded file"))

    uploaded_file = None

    if file_option == "Upload a new file":
        uploaded_file = st.file_uploader("Choose a CSV file to begin analysis", type="csv")

        # Check if a file is already successfully uploaded and stored in session state
        if uploaded_file is not None and "uploaded_file_id" not in st.session_state:
            # Store the file in session state
            st.session_state.uploaded_file = uploaded_file

            # Upload the file to the API
            uploaded_file.seek(0)  # Reset file pointer
            files = {"file": uploaded_file}
            response = requests.post(f"{API_BASE_URL}/upload_file", files=files)

            if response.status_code == 200:
                st.success("File uploaded successfully!")
                file_id = response.json()["id"]

                # Store the file ID in session state to avoid re-uploading
                st.session_state.uploaded_file_id = file_id

                # Immediately fetch the file back from the database
                file_response = requests.get(f"{API_BASE_URL}/get_file/{file_id}")
                if file_response.status_code == 200:
                    file_data = file_response.json()

                    # Extract file content and filename
                    file_content = file_data["content"].encode('latin1')  # Convert back to bytes

                    # Treat it as a file-like object and save it to session state
                    uploaded_file = BytesIO(file_content)
                    uploaded_file.name = file_data["filename"]  # Set the filename attribute
                    st.session_state.uploaded_file = uploaded_file  # Save in session state

                else:
                    st.error(f"Failed to fetch file with ID {file_id}.")
            elif response.status_code == 409:  # Handle duplicate file
                st.warning("A file with this name already exists. Please upload a different file.")
                return  # Stop further processing
            else:
                st.error("Failed to upload file.")
    elif file_option == "Select a previously uploaded file":
        # Get list of previously uploaded files
        response = requests.get(f"{API_BASE_URL}/list_files")
        if response.status_code == 200:
            files = response.json()
            if not files:  # Check if the list is empty
                st.warning("No files have been uploaded yet.")
                return

            file_names = [file["filename"] for file in files]
            selected_file = st.selectbox("Select a previously uploaded file", file_names)

            if selected_file:
                try:
                    file_id = next(file["id"] for file in files if file["filename"] == selected_file)

                    # Store the file ID in session state
                    st.session_state.uploaded_file_id = file_id

                    # Fetch the selected file from the API
                    file_response = requests.get(f"{API_BASE_URL}/get_file/{file_id}")
                    if file_response.status_code == 200:
                        file_data = file_response.json()

                        # Extract file content and filename
                        file_content = bytes(file_data["content"], 'latin1')  # Convert back to bytes

                        # Treat it as a file-like object and save it to session state
                        uploaded_file = BytesIO(file_content)
                        uploaded_file.name = file_data["filename"]  # Set the filename attribute
                        st.session_state.uploaded_file = uploaded_file  # Save in session state

                    else:
                        st.error(f"Failed to fetch file with ID {file_id}.")
                except StopIteration:
                    st.error(f"No file found with the name '{selected_file}'. Please try again.")
        else:
            st.error("Failed to retrieve file list.")

    # Retrieve the uploaded file from session state if available
    uploaded_file = st.session_state.get("uploaded_file", None)

    if "analysis_complete" not in st.session_state:
        st.session_state.analysis_complete = False
    if "num_duplicates" not in st.session_state:
        st.session_state.num_duplicates = 0
    if "duplicates_removed" not in st.session_state:
        st.session_state.duplicates_removed = False
    if "deduplicated_data_ready" not in st.session_state:
        st.session_state.deduplicated_data_ready = False
    if "previous_uploaded_file" not in st.session_state:
        st.session_state.previous_uploaded_file = None
    if "navbar_selection" not in st.session_state:
        st.session_state.navbar_selection = "Unique ID Verifier"
    if "drop_export_complete" not in st.session_state:
        st.session_state.drop_export_complete = False

    def reset_session_states():
        st.session_state.analysis_complete = False
        st.session_state.num_duplicates = 0
        st.session_state.duplicates_removed = False
        st.session_state.deduplicated_data_ready = False

    if uploaded_file is not None:
        if uploaded_file != st.session_state.previous_uploaded_file:
            reset_session_states()
            st.session_state.previous_uploaded_file = uploaded_file
        # Run preliminary tests
        with st.spinner("Running preliminary tests on the uploaded file..."):
            try:
                files = {"file": ("uploaded_file.csv", uploaded_file, "text/csv")}
                response = requests.post(PRELIMINARY_TESTS_ENDPOINT, files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    if result["status"] == 0:
                        st.success("Preliminary tests passed successfully!")
                        if result["warnings"]:
                            st.warning("Warnings:")
                            for warning in result["warnings"]:
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(f"- {warning}")
                                with col2:
                                    relevant_func = get_relevant_functionality(warning)
                                    if st.button(f"Check {relevant_func}", key=f"warning_button_{warning}"):
                                        st.session_state.navbar_selection = relevant_func

                        # Try to read the CSV file
                        try:
                            uploaded_file.seek(0)  # Reset file pointer
                            df = pd.read_csv(uploaded_file)
                            df.columns = df.columns.str.strip().str.lower()  # Convert to lowercase and strip whitespace
                            st.write("Data Preview:")
                            st.dataframe(df.head())
                        except Exception as e:
                            st.error(f"Error reading the CSV file: {str(e)}")
                            st.write("Unable to display data preview.")

                        # Sidebar for functionality selection
                        st.sidebar.header("Select Functionality")
                        functionality = st.sidebar.selectbox(
                            "Choose a functionality",
                            [
                                "Unique ID Verifier",
                                "Check Specific Columns as Unique ID",
                                "Drop/Export Duplicate Entries",
                                "Drop/Export Duplicate Rows",
                                "Missing Entries Analysis",
                                "Zero Entries Analysis",
                                "Indicator Fill Rate Analysis",
                                "Frequency Table Analysis"
                            ],
                            key="navbar_selection"
                        )
                        
                        functionality = st.session_state.navbar_selection
                        
                        if functionality == "Unique ID Verifier":
                            st.session_state.drop_export_complete = False
                            st.subheader("Unique ID Verifier")
                            st.write("Use this feature to let the system identify the list of unique IDs in the dataset.")
                            with st.expander("ℹ️ Info"):
                                st.markdown("""
                                - Numerical columns, or combinations which are comprised of more numerical columns, will be given precedence while displaying the output.
                                - If you have also used any of the other modules before, you can also use the same dataset used there by clicking the "Use existing dataset" button below.
                                - Valid input format for dataset: xlsx or csv
                                - A minimum of ONE column has to be selected
                                - Max no. of selectable columns: As many as the number of column headers
                                """)
                            if st.button("Find Unique IDs"):
                                with st.spinner("Finding unique IDs..."):
                                    try:
                                        uploaded_file.seek(0)
                                        files = {"file": ("uploaded_file.csv", uploaded_file, "text/csv")}
                                        response = requests.post(FIND_UNIQUE_IDS_ENDPOINT, files=files)
                                        
                                        if response.status_code == 200:
                                            unique_ids = response.json()
                                            
                                            if unique_ids:
                                                st.success("Unique IDs found!")
                                                st.write("The best possible Column(s) or Combinations that can act as Unique ID are as follows:")
                                                df = pd.DataFrame(unique_ids)
                                                df['UniqueID'] = df['UniqueID'].apply(lambda x: ' + '.join(x))
                                                df = df.rename(columns={'UniqueID': 'Unique ID', 'Numeric_DataTypes': 'Is Numeric'})
                                                st.dataframe(df, use_container_width=True)
                                            else:
                                                st.warning("No unique identifiers found. All columns or combinations have at least one duplicate.")
                                        else:
                                            st.error(f"Error: {response.status_code} - {response.text}")
                                            st.write("Response content:", response.content)
                                            st.write("Response headers:", response.headers)
                                    except Exception as e:
                                        st.error(f"An error occurred: {str(e)}")
                                        st.write("Traceback:", traceback.format_exc())

                        elif functionality == "Check Specific Columns as Unique ID":
                            st.session_state.drop_export_complete = False
                            st.subheader("Check Specific Columns as Unique ID")
                            st.write("Use this feature to check whether the column(s) you think form the unique ID is indeed the unique ID.")
                            with st.expander("ℹ️ Info"):
                                st.markdown("""
                                - Verifies if selected column(s) can serve as a unique identifier for the dataset.
                                - You can select up to 4 columns to check.
                                - The function will return whether the selected column(s) can work as a unique ID.
                                - Valid input format: CSV file
                                - A minimum of ONE column must be selected.
                                """)
                            columns = st.multiselect("Select columns to check", options=df.columns.tolist())
                            
                            if columns and st.button("Check Unique ID"):
                                with st.spinner("Checking unique ID..."):
                                    df_clean = df.replace([np.inf, -np.inf], np.nan).dropna()
                                    data = df_clean.where(pd.notnull(df_clean), None).to_dict('records')
                                    payload = {"data": data, "columns": columns}
                                    response = requests.post(UNIQUE_ID_CHECK_ENDPOINT, json=payload)
                                    
                                    if response.status_code == 200:
                                        result = response.json()['result']
                                        if result[1]:
                                            st.success("Check completed!")
                                            st.write(result[0])
                                        else:
                                            st.warning(result[0])
                                            st.write("Go to Unique ID Verifier to check for column uniqueness")
                                    else:
                                        error_detail = response.json().get("detail", "Unknown error")
                                        st.error(f"Error: {response.status_code} - {error_detail}")

                        elif functionality == "Drop/Export Duplicate Entries":
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

                        elif functionality == "Drop/Export Duplicate Rows":
                            st.session_state.drop_export_complete = False
                            st.subheader("Drop/Export Duplicate Rows")
                            st.write("This function checks for fully duplicate rows in the dataset and returns the number and percentage of such duplicated rows in the dataset.")
                            with st.expander("ℹ️ Info"):
                                st.markdown("""
                                - Analyzes the dataset to find the number and percentage of completely duplicated rows.
                                - Uses different methods for small and large datasets to ensure efficient processing.
                                - Provides the count and percentage of duplicate rows in the dataset.
                                - Offers options to remove duplicate rows.
                                - Valid input format: CSV file
                                """)

                            # Analyze Duplicates
                            if st.button("Analyze Duplicates") and not st.session_state.analysis_complete:
                                with st.spinner("Analyzing duplicates..."):
                                    try:
                                        uploaded_file.seek(0)
                                        files = {"file": ("uploaded_file.csv", uploaded_file, "text/csv")}
                                        response = requests.post(DUPLICATE_ANALYSIS_ENDPOINT, files=files)

                                        if response.status_code == 200:
                                            result = response.json()
                                            st.success("Analysis complete!")
                                            st.write(f"Number of duplicates: {result['num_duplicates']}")
                                            st.write(f"Percentage of duplicates: {result['percent_duplicates']:.2f}%")
                                            st.session_state.analysis_complete = True
                                            st.session_state.num_duplicates = result['num_duplicates']

                                            # Pie Chart
                                            labels = ['Unique Rows', 'Duplicate Rows']
                                            values = [100 - result['percent_duplicates'], result['percent_duplicates']]
                                            fig = plot_pie_chart(labels, values, "Unique vs Duplicate Rows Distribution")
                                            st.plotly_chart(fig)
                                        else:
                                            st.error(f"Error: {response.status_code} - {response.text}")
                                    except Exception as e:
                                        st.error(f"An error occurred: {str(e)}")

                            # Show analysis results if complete
                            if st.session_state.analysis_complete:
                                st.write(f"Number of duplicates: {st.session_state.num_duplicates}")

                            # Remove Duplicates
                            if st.session_state.analysis_complete and st.session_state.num_duplicates > 0:
                                remove_option = st.selectbox(
                                    "Select how to handle duplicates:",
                                    ["Keep first occurrence", "Drop all occurrences"]
                                )

                                # Get the original filename without extension
                                original_filename = uploaded_file.name.rsplit('.', 1)[0]

                                # Input field for custom filename
                                custom_filename = st.text_input(
                                    "Enter a name for your deduplicated file (optional)",
                                    value=f"{original_filename}_deduplicated.csv"
                                )

                                # Ensure the filename ends with .csv
                                if not custom_filename.lower().endswith('.csv'):
                                    custom_filename += '.csv'

                                if not st.session_state.duplicates_removed:
                                    if st.button("Remove Duplicate Rows", key="remove_duplicates_button"):
                                        with st.spinner("Removing duplicate rows..."):
                                            try:
                                                uploaded_file.seek(0)  # Reset the file pointer
                                                files = {"file": ("uploaded_file.csv", uploaded_file, "text/csv")}
                                                remove_response = requests.post(
                                                    REMOVE_DUPLICATES_ENDPOINT,
                                                    files=files,
                                                    data={"remove_option": remove_option}
                                                )

                                                if remove_response.status_code == 200:
                                                    remove_result = remove_response.json()
                                                    st.success("Duplicate rows removed successfully!")
                                                    st.write(f"Original row count: {remove_result['original_count']}")
                                                    st.write(f"Deduplicated row count: {remove_result['deduplicated_count']}")
                                                    st.write(f"Dropped row count: {remove_result['dropped_count']}")
                                                    st.session_state.duplicates_removed = True
                                                    st.session_state.deduplicated_data_ready = True
                                                else:
                                                    st.error(f"Error: {remove_response.status_code} - {remove_response.text}")
                                            except Exception as e:
                                                st.error(f"An error occurred: {str(e)}")

                                # Download Deduplicated Data
                                if st.session_state.deduplicated_data_ready:
                                    deduped_response = requests.get(
                                        GET_DEDUPLICATED_DATA_ENDPOINT,
                                        params={"filename": custom_filename}
                                    )
                                    if deduped_response.status_code == 200:
                                        deduped_data = deduped_response.content
                                        if st.download_button(
                                            label="Download Deduplicated Data",
                                            data=deduped_data,
                                            file_name=custom_filename,
                                            mime="text/csv"
                                        ):
                                            st.warning("Please consider uploading the newly downloaded deduplicated file for further analysis.")
                                    else:
                                        st.error("Failed to retrieve deduplicated data.")

                        elif functionality == "Missing Entries Analysis":
                            st.session_state.drop_export_complete = False
                            st.subheader("Missing Entries Analysis")
                            st.write("This function returns the count and percentage of missing values for a given variable, with optional filtering and grouping by a categorical variable.")
                            with st.expander("ℹ️ Info"):
                                st.markdown("""
                                - Analyzes the dataset to find missing entries in a specified column.
                                - Optionally groups or filters the analysis by other categorical columns.
                                - Provides a table of rows with missing entries.
                                - Valid input format: CSV file
                                """)

                            column_to_analyze = st.selectbox("Select column to analyze for missing entries:", options=df.columns.tolist(), index=0)
                            group_by = st.selectbox("Group by (optional): Analyze missing entries within distinct categories of another column. This is useful if you want to understand how missing values are distributed across different groups.", options=["None"] + df.columns.tolist(), index=0)
                            filter_by_col = st.selectbox("Filter by column (optional): Focus on a specific subset of your data by selecting a specific value in another column. This is helpful when you want to analyze missing entries for a specific condition.", options=["None"] + df.columns.tolist(), index=0)

                            if filter_by_col != "None":
                                filter_by_value = st.selectbox("Filter value", df[filter_by_col].unique().tolist())
                            else:
                                filter_by_value = None

                            # Analyze Missing Entries
                            if st.button("Analyze Missing Entries"):
                                with st.spinner("Analyzing missing entries..."):
                                    try:
                                        uploaded_file.seek(0)  # Reset file pointer
                                        files = {"file": ("uploaded_file.csv", uploaded_file, "text/csv")}
                                        payload = {
                                            "column_to_analyze": column_to_analyze,
                                            "group_by": group_by if group_by != "None" else None,
                                            "filter_by": {filter_by_col: filter_by_value} if filter_by_col != "None" else None
                                        }
                                        response = requests.post(
                                            MISSING_ENTRIES_ENDPOINT,
                                            files=files,
                                            data={"input_data": json.dumps(payload)}
                                        )
                                                                            
                                        if response.status_code == 200:
                                            result = response.json()
                                            st.success("Analysis complete!")
                                            
                                            if result["grouped"]:
                                                st.write("Missing entries by group:")
                                                grouped_data = []
                                                for group, (count, percentage) in result["analysis"].items():
                                                    grouped_data.append({
                                                        group_by: group,  # Use the name of the group-by column
                                                        "Missing Count": count,
                                                        "Missing Percentage": f"{percentage:.2f}%" if percentage is not None else "N/A"
                                                    })
                                                
                                                grouped_df = pd.DataFrame(grouped_data)
                                                grouped_df = grouped_df.sort_values("Missing Count", ascending=False)
                                                
                                                # Center-align just Missing Count and Missing Percentage
                                                st.dataframe(grouped_df.style.set_properties(**{
                                                    'text-align': 'center',
                                                    'text': 'center',
                                                    'align-items': 'center',
                                                    'justify-content': 'center'
                                                }, subset=['Missing Count', 'Missing Percentage']), use_container_width=True)
                                                
                                                # Create a 100% stacked column chart
                                                data = pd.DataFrame([(group, percentage, 100-percentage if percentage is not None else 0) 
                                                                    for group, (count, percentage) in result["analysis"].items()],
                                                                    columns=[group_by, 'Missing', 'Present'])
                                                data = data.sort_values('Missing', ascending=False)
                                                fig = px.bar(data, x=group_by, y=['Missing', 'Present'], 
                                                            title=f"Missing vs Present Entries by {group_by}",
                                                            labels={'value': 'Percentage', 'variable': 'Status'},
                                                            color_discrete_map={'Missing': 'red', 'Present': 'green'},
                                                            text='value')
                                                fig.update_layout(barmode='relative', yaxis_title='Percentage')
                                                fig.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
                                                st.plotly_chart(fig)
                                            else:
                                                count, percentage = result["analysis"]
                                                if percentage is not None:
                                                    st.write(f"Missing entries: {count} ({percentage:.2f}%)")
                                                    labels = ['Missing', 'Present']
                                                    values = [percentage, 100-percentage]
                                                    fig = plot_pie_chart(labels, values, "Missing vs Present Entries (%)")
                                                    st.plotly_chart(fig)
                                                else:
                                                    st.write(f"Missing entries: {count} (percentage unavailable)")
                                            
                                            if result["filtered"]:
                                                st.info(f"Results are filtered by {filter_by_col} = {filter_by_value}")
                                                
                                            # Display the table of missing entries
                                            if "missing_entries_table" in result:
                                                if not result["missing_entries_table"]:
                                                    st.warning("The missing entries table is empty. There might be no missing entries, or an issue occurred.")
                                                else:
                                                    missing_entries_df = pd.DataFrame(result["missing_entries_table"])
                                                                                            
                                                    if column_to_analyze in missing_entries_df.columns:
                                                        missing_entries_df = missing_entries_df.sort_values(column_to_analyze, ascending=False)
                                                        st.success(f"Sorted by column: '{column_to_analyze}'")
                                                    else:
                                                        st.warning(f"Column '{column_to_analyze}' not found in the missing entries table. Displaying unsorted data.")
                                                    
                                                    st.write("Rows with Missing Entries:")
                                                    st.dataframe(missing_entries_df, use_container_width=True)
                                            else:
                                                st.error("The 'missing_entries_table' key is not present in the API response.")

                                        else:
                                            error_detail = response.json().get("detail", "Unknown error")
                                            st.error(f"Error: {response.status_code} - {error_detail}")
                                    except Exception as e:
                                        st.error(f"An error occurred: {str(e)}")
                                        st.write("Traceback:", traceback.format_exc())

                        elif functionality == "Zero Entries Analysis":
                            st.session_state.drop_export_complete = False
                            st.subheader("Zero Entries Analysis")
                            st.write("The function returns the count and percentage of zero values for a variable, with optional filtering and grouping by a categorical variable.")
                            with st.expander("ℹ️ Info"):
                                st.markdown("""
                                - Analyzes zero entries in a specified column of the dataset.
                                - Options:
                                - Select a column to analyze
                                - Optionally group by a categorical variable
                                - Optionally filter by a categorical variable
                                - Provides the count and percentage of zero entries.
                                - Displays a table of rows with zero entries.
                                - Valid input format: CSV file
                                """)
                            
                            column_to_analyze = st.selectbox("Select column to analyze", df.columns.tolist())
                            group_by = st.selectbox("Group by (optional): Analyze missing entries within distinct categories of another column. This is useful if you want to understand how missing values are distributed across different groups.", ["None"] + df.columns.tolist())
                            filter_by_col = st.selectbox("Filter by (optional): Focus on a specific subset of your data by selecting a specific value in another column. This is helpful when you want to analyze missing entries for a specific condition.", ["None"] + df.columns.tolist())
                            
                            if filter_by_col != "None":
                                filter_by_value = st.selectbox("Filter value", df[filter_by_col].unique().tolist())
                            
                            if st.button("Analyze Zero Entries"):
                                with st.spinner("Analyzing zero entries..."):
                                    try:
                                        uploaded_file.seek(0)  # Reset file pointer
                                        files = {"file": ("uploaded_file.csv", uploaded_file, "text/csv")}
                                        payload = {
                                            "column_to_analyze": column_to_analyze,
                                            "group_by": group_by if group_by != "None" else None,
                                            "filter_by": {filter_by_col: filter_by_value} if filter_by_col != "None" else None
                                        }
                                        response = requests.post(
                                            ZERO_ENTRIES_ENDPOINT,
                                            files=files,
                                            data={"input_data": json.dumps(payload)}
                                        )
                                        
                                        if response.status_code == 200:
                                            result = response.json()
                                            st.success("Analysis complete!")
                                            
                                            if result["grouped"]:
                                                st.write("Zero entries by group:")
                                                group_column_name = group_by  # Use the selected group-by column name
                                                grouped_data = [{group_column_name: group, "Zero Count": count, "Zero Percentage": f"{percentage:.2f}%"}
                                                                for group, (count, percentage) in result["analysis"].items()]
                                                grouped_df = pd.DataFrame(grouped_data)
                                                grouped_df = grouped_df.sort_values("Zero Count", ascending=False)
                                                st.dataframe(grouped_df, use_container_width=True)
                                                
                                                data = pd.DataFrame([(group, percentage, 100-percentage) for group, (count, percentage) in result["analysis"].items()],
                                                                    columns=[group_column_name, 'Zero', 'Non-Zero'])
                                                data = data.sort_values('Zero', ascending=False)
                                                fig = px.bar(data, x=group_column_name, y=['Zero', 'Non-Zero'], 
                                                            title=f"Zero vs Non-Zero Entries by {group_column_name}",
                                                            labels={'value': 'Percentage', 'variable': 'Entry Type'},
                                                            color_discrete_map={'Zero': '#1f77b4', 'Non-Zero': '#ff7f0e'})
                                                fig.update_layout(barmode='relative', yaxis_title='Percentage')
                                                fig.update_traces(texttemplate='%{y:.1f}%', textposition='inside')
                                                st.plotly_chart(fig)
                                            else:
                                                count, percentage = result["analysis"]
                                                analysis_df = pd.DataFrame([{"Zero Count": count, "Zero Percentage": f"{percentage:.2f}%"}])
                                                st.dataframe(analysis_df, use_container_width=True)
                                                
                                                labels = ['Zero', 'Non-Zero']
                                                values = [percentage, 100-percentage]
                                                fig = plot_pie_chart(labels, values, "Zero vs Non-Zero Entries (%)")
                                                st.plotly_chart(fig)
                                            
                                            if result["filtered"]:
                                                st.info(f"Results are filtered by {filter_by_col} = {filter_by_value}")
                                            
                                            # Display the table of zero entries
                                            if "zero_entries_table" in result:
                                                zero_entries_df = pd.DataFrame(result["zero_entries_table"])
                                                if column_to_analyze in zero_entries_df.columns:
                                                    zero_entries_df = zero_entries_df.sort_values(column_to_analyze, ascending=False)
                                                else:
                                                    st.warning(f"Column '{column_to_analyze}' not found in the zero entries table. Displaying unsorted data.")
                                                st.write("Rows with Zero Entries:")
                                                st.dataframe(zero_entries_df, use_container_width=True)
                                        else:
                                            st.error(f"Error: {response.status_code} - {response.text}")
                                    except Exception as e:
                                        st.error(f"An error occurred: {str(e)}")
                                        st.write("Traceback:", traceback.format_exc())

                        elif functionality == "Indicator Fill Rate Analysis":
                            st.session_state.drop_export_complete = False
                            st.subheader("Indicator Fill Rate Analysis")
                            st.write("This function analyzes a variable for missing, zero, and other invalid values, returning counts and percentages in a table format, with optional filtering or grouping by a categorical variable and customizable invalid value conditions (e.g., value > x).")
                            with st.expander("ℹ️ Info"):
                                st.markdown("""
                                - Analyzes the fill rate and data quality of a specified column in the dataset.
                                - Options:
                                - Select a column to analyze
                                - Optionally group by a categorical variable
                                - Optionally filter by a categorical variable
                                - Specify a custom condition for invalid values
                                - Provides counts and percentages for missing, zero, invalid, and valid values.
                                - Displays samples of missing, zero, invalid, and valid data.
                                - Valid input format: CSV file
                                """)

                            def is_numeric_column(series):
                                return pd.api.types.is_numeric_dtype(series) or series.dtype == 'object' and series.str.isnumeric().all()

                            def is_string_column(series):
                                return pd.api.types.is_string_dtype(series)

                            def is_datetime_column(series):
                                if pd.api.types.is_datetime64_any_dtype(series):
                                    return True
                                
                                # Try to parse the first non-null value as a date
                                first_valid = series.first_valid_index()
                                if first_valid is not None:
                                    try:
                                        pd.to_datetime(series[first_valid])
                                        return True
                                    except:
                                        pass
                                
                                return False

                            def get_numeric_operations():
                                return ['<', '<=', '>', '>=', '==', '!=']

                            def get_string_operations():
                                return ['Contains', 'Does not contain']
                            
                            column_to_analyze = st.selectbox("Select column to analyze", df.columns.tolist())
                            group_by = st.selectbox("Group by (optional)", ["None"] + df.columns.tolist())
                            filter_by_col = st.selectbox("Filter by (optional)", ["None"] + df.columns.tolist())
                            
                            if filter_by_col != "None":
                                filter_by_value = st.selectbox("Filter value", df[filter_by_col].unique().tolist())
                            
                            if is_numeric_column(df[column_to_analyze]):
                                st.write("Set condition for invalid values:")
                                col1, col2 = st.columns(2)
                                with col1:
                                    operation = st.selectbox("Operation", get_numeric_operations())
                                with col2:
                                    threshold = st.number_input("Threshold", value=0.0, step=0.1)
                                invalid_condition = f"{operation} {threshold}"
                                include_zero_as_separate_category = st.checkbox("Include zero entries as a separate category", value=True)
                            elif is_string_column(df[column_to_analyze]):
                                st.write("Set condition for invalid string values:")
                                col1, col2 = st.columns(2)
                                with col1:
                                    operation = st.selectbox("Operation", get_string_operations())
                                with col2:
                                    value = st.selectbox("Value", df[column_to_analyze].unique().tolist())
                                invalid_condition = (operation, value)
                                include_zero_as_separate_category = False
                            elif is_datetime_column(df[column_to_analyze]):
                                st.write("Set condition for invalid datetime values:")
                                col1, col2 = st.columns(2)
                                with col1:
                                    start_date = st.date_input("Start date(Exclusive)")
                                with col2:
                                    end_date = st.date_input("End date(Inclusive)")
                                invalid_condition = (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                                include_zero_as_separate_category = False
                            else:
                                st.write("The column should include either numbers, strings, or dates.")
                                invalid_condition = None

                            if st.button("Analyze Indicator Fill Rate"):
                                with st.spinner("Analyzing indicator fill rate..."):
                                    try:
                                        uploaded_file.seek(0)  # Reset file pointer
                                        files = {"file": ("uploaded_file.csv", uploaded_file, "text/csv")}
                                        payload = {
                                            "column_to_analyze": column_to_analyze,
                                            "group_by": group_by if group_by != "None" else None,
                                            "filter_by": {filter_by_col: filter_by_value} if filter_by_col != "None" else None,
                                            "invalid_condition": invalid_condition,
                                            "include_zero_as_separate_category": include_zero_as_separate_category
                                        }
                                        response = requests.post(
                                            INDICATOR_FILL_RATE_ENDPOINT,
                                            files=files,
                                            data={"input_data": json.dumps(payload)}
                                        )
                                        
                                        if response.status_code == 200:
                                            result = response.json()
                                            st.success("Analysis complete!")
                                            
                                            def display_detailed_data(data):
                                                if include_zero_as_separate_category:
                                                    for category in ["missing", "zero", "invalid", "valid"]:
                                                        if data[category]:
                                                            st.write(f"{category.capitalize()} data (up to 10 rows):")
                                                            category_df = pd.DataFrame(data[category])
                                                            st.dataframe(category_df, use_container_width=True)
                                                        else:
                                                            st.write(f"No {category} data found.")
                                                else:
                                                    for category in ["missing", "invalid", "valid"]:
                                                        if data[category]:
                                                            st.write(f"{category.capitalize()} data (up to 10 rows):")
                                                            category_df = pd.DataFrame(data[category])
                                                            st.dataframe(category_df, use_container_width=True)
                                                        else:
                                                            st.write(f"No {category} data found.")

                                            def prepare_data_for_plotting(analysis_df):
                                                plot_data = analysis_df.reset_index()
                                                if len(plot_data.columns) == 4:
                                                    if include_zero_as_separate_category:
                                                        plot_data.columns = ['Index', 'Category', 'Count', 'Percentage']
                                                    else:
                                                        plot_data = plot_data[plot_data['Category'] != 'Zero']
                                                        plot_data.columns = ['Index', 'Category', 'Count', 'Percentage']
                                                elif len(plot_data.columns) == 3:
                                                    if include_zero_as_separate_category:
                                                        plot_data.columns = ['Category', 'Count', 'Percentage']
                                                    else:
                                                        plot_data = plot_data[plot_data['Category'] != 'Zero']
                                                        plot_data.columns = ['Category', 'Count', 'Percentage']
                                                else:
                                                    raise ValueError(f"Unexpected number of columns: {len(plot_data.columns)}")
                                                plot_data = plot_data.sort_values('Count', ascending=False)
                                                return plot_data
                                            
                                            if result["grouped"]:
                                                st.write("Indicator Fill Rate by group:")
                                                # Prepare data for 100% stacked column chart
                                                all_groups_data = []
                                                for group, analysis in result["analysis"].items():
                                                    analysis_df = pd.DataFrame(analysis)
                                                    analysis_df['Group'] = group
                                                    all_groups_data.append(analysis_df)
                                                combined_df = pd.concat(all_groups_data, ignore_index=True)
                                                # Calculate percentages within each group
                                                combined_df['Percentage'] = combined_df.groupby('Group')['Count'].transform(lambda x: x / x.sum() * 100)
                                                # Create the 100% stacked column chart
                                                fig = plot_100_stacked_bar_chart(combined_df, x='Group', y='Percentage', color='Category',
                                                                                title="Indicator Fill Rate by Group",
                                                                                x_label=group_by, y_label="Percentage")
                                                st.plotly_chart(fig)

                                                # Display detailed data for each group
                                                for group, analysis in result["analysis"].items():
                                                    st.write(f"Group: {group}")
                                                    analysis_df = pd.DataFrame(analysis)
                                                    st.dataframe(analysis_df, use_container_width=True)
                                                    display_detailed_data(result["detailed_data"][group])
                                                    st.write("---")
                                            else:
                                                st.write("Indicator Fill Rate:")
                                                analysis_df = pd.DataFrame(result["analysis"])
                                                st.dataframe(analysis_df, use_container_width=True)
                                                # Create a simple pie chart of percentages
                                                fig = plot_pie_chart(labels=analysis_df['Category'], 
                                                                    values=analysis_df['Percentage'], 
                                                                    title="Indicator Fill Rate")
                                                st.plotly_chart(fig)

                                                display_detailed_data(result["detailed_data"])

                                            if result["filtered"]:
                                                st.info(f"Results are filtered by {filter_by_col} = {filter_by_value}")
                                            
                                            if invalid_condition:
                                                st.info(f"Custom invalid condition applied: {invalid_condition}")
                                        else:
                                            st.error(f"Error: {response.status_code} - {response.text}")
                                    except Exception as e:
                                        st.error(f"An error occurred: {str(e)}")
                                        st.write("Traceback:", traceback.format_exc())

                        elif functionality == "Frequency Table Analysis":
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
                                                    st.dataframe(top_n_df, use_container_width=True)
                                                else:
                                                    st.write("All Frequency Values:")
                                                    full_df = pd.DataFrame(full_table)
                                                    full_df = full_df[[column_to_analyze, group_by, "count", "share %"]]
                                                    full_df = full_df.sort_values("count", ascending=False)
                                                    st.dataframe(full_df, use_container_width=True)

                                            else:
                                                full_table, top_n_table = result["analysis"]
                                                if top_n > 0:
                                                    st.write(f"Top {top_n} frequent values:")
                                                    top_n_df = pd.DataFrame(top_n_table)
                                                    top_n_df = top_n_df.sort_values("count", ascending=False)
                                                    top_n_df.columns = [column_to_analyze, "count", "share %"]
                                                    st.dataframe(top_n_df, use_container_width=True)
                                                else:
                                                    full_df = pd.DataFrame(full_table)
                                                    full_df.columns = [column_to_analyze, "count", "share %"]
                                                    full_df = full_df.sort_values("count", ascending=False)
                                                    st.dataframe(full_df, use_container_width=True)

                                            if result["filtered"]:
                                                st.info(f"Results are filtered by {filter_by_col} = {filter_by_value}")
                                        else:
                                            st.error(f"Error: {response.status_code} - {response.text}")
                                    except Exception as e:
                                        st.error(f"An error occurred: {str(e)}")
                                        st.write("Traceback:", traceback.format_exc())

                    else:
                        st.error(f"Error: {result['message']}")
                
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.write("Traceback:", traceback.format_exc())

    else:
        st.info("Please upload a CSV file to begin.")
        reset_session_states()
        st.session_state.previous_uploaded_file = None

    if st.session_state.get('reset_upload', False):
        st.session_state.reset_upload = False
        st.session_state.analysis_complete = False
        st.session_state.num_duplicates = 0
        st.session_state.duplicates_removed = False
        st.session_state.deduplicated_data_ready = False
        st.session_state.previous_uploaded_file = None
        st.rerun()

def pre_survey_analysis():
    st.title("Pre-survey Analysis")

    # Homepage content
    st.write("""
    Welcome to the Pre-survey Analysis module. This module helps you determine optimal sample sizes and sampling strategies for your survey. Choose from the following options:
    
    1. L1 Sample Size Calculator: Estimate the supervisor sample size required to guarantee identification of outlier subordinates.
    2. L2 Sample Size Calculator: Calculate the optimal sample size for measuring discrepancy at different administrative levels.
    3. 3P Sampling Strategy Predictor: Determine the best strategy for third-party sampling given resource constraints.
    
    Select an option from the sidebar to get started.
    """)

    st.sidebar.header("Pre-survey Analysis Options")

    L1_SAMPLE_SIZE_ENDPOINT = f"{API_BASE_URL}/l1-sample-size"
    L2_SAMPLE_SIZE_ENDPOINT = f"{API_BASE_URL}/l2-sample-size"
    THIRD_PARTY_SAMPLING_ENDPOINT = f"{API_BASE_URL}/third-party-sampling"
    ERROR_HANDLING_ENDPOINT = f"{API_BASE_URL}/error-handling"

    def check_errors(params):
        response = requests.post(ERROR_HANDLING_ENDPOINT, json={"params": params})
        if response.status_code == 200:
            result = response.json()
            return result["status"], result["message"]
        else:
            return 0, f"Error in error handling: {response.json()['detail']}"

    def l1_sample_size_calculator():
        st.subheader("L1 Sample Size Calculator")
        
        # Input fields
        min_n_samples = st.number_input("Minimum number of samples: The minimum number of data points that a supervisor will sample (typically 1). Range > 0", min_value=1, value=1)
        max_n_samples = st.number_input("Maximum number of samples: The maximum number of data points that a supervisor can sample (if this is not high enough, the guarantee may not be possible and the algorithm will ask you to increase this). Range > min_n_samples", min_value=min_n_samples + 1, value=100)
        n_subs_per_block = st.number_input("Number of subordinates per block: The number of subordinates that one supervisor will test. Range > 0", min_value=1, value=10)
        n_blocks_per_district = st.number_input("Number of blocks per district", min_value=1, value=5)
        n_district = st.number_input("Number of districts", min_value=1, value=1)
        level_test = st.selectbox("Level of test", ["Block", "District", "State"])
        percent_punish = st.slider("Percentage of subordinates to be punished: The percentage of subordinates that will be punished. This should be less than 100% (the total number of subordinates). The higher this number, the easier it is to guarantee that worst offenders will be caught, so increase this if the number of samples being returned is too high. 0 < Range <= 100", min_value=0.0, max_value=100.0, value=10.0)
        percent_guarantee = st.slider("Percentage of worst offenders guaranteed: The percentage of worst offenders that we can guarantee will be present in the set of subordinates that are punished. The closer this number is to n_punish, the more difficult it is to guarantee, so decrease this if the number of samples being returned is too high.  0 < Range <= 100", min_value=0.0, max_value=percent_punish, value=5.0)
        confidence = st.slider("Confidence: The probability that n_guarantee worst offenders will be present in the set of n_punish subordinates with highest discrepancy scores. The higher this probability, the more difficult it is to guarantee, so decrease this if the number of samples being returned is too high. 0 < Range < 1", min_value=0.0, max_value=1.0, value=0.9)
        n_simulations = st.number_input("Number of simulations: By default, this should be set to 100. The number of times the algorithm will be run to estimate the number of samples required. Higher n_simulations will give a more accurate answer, but will take longer to run. Range > 1", min_value=1, value=100)
        min_disc = st.slider("Minimum discrepancy score: Minimum discrepancy score to be used for simulation. By default, set to 0 (no discrepancy between subordinate and supervisor). If you are working with a sector in which you have reason to believe the lowest observed discrepancy scores are higher than 0, set it to that number. 0 < Range < 1", min_value=0.0, max_value=1.0, value=0.0)
        max_disc = st.slider("Maximum discrepancy score: Maximum discrepancy score to be used for simulation. By default, set to 1 (100% discrepancy between subordinate and supervisor). If you are working with a sector in which you have reason to believe the highest observed discrepancy scores are lower than 1, set it to that number. min_disc < Range < 1", min_value=min_disc, max_value=1.0, value=1.0)
        mean_disc = st.slider("Mean discrepancy score", min_value=min_disc, max_value=max_disc, value=(min_disc + max_disc) / 2)
        std_disc = st.slider("Standard deviation of discrepancy score", min_value=0.0, max_value=(max_disc - min_disc) / 2, value=(max_disc - min_disc) / 4)
        distribution = st.selectbox("Distribution: Distribution of discrepancy scores to be used for simulation. Currently, only uniform distribution is implemented. We will implement normal and other distributions in future versions.", ["uniform", "normal"])

        if st.button("Calculate L1 Sample Size"):
            input_data = {
                "min_n_samples": min_n_samples,
                "max_n_samples": max_n_samples,
                "n_subs_per_block": n_subs_per_block,
                "n_blocks_per_district": n_blocks_per_district,
                "n_district": n_district,
                "level_test": level_test,
                "percent_punish": percent_punish,
                "percent_guarantee": percent_guarantee,
                "confidence": confidence,
                "n_simulations": n_simulations,
                "min_disc": min_disc,
                "max_disc": max_disc,
                "mean_disc": mean_disc,
                "std_disc": std_disc,
                "distribution": distribution
            }
            
            # Error handling
            error_status, error_message = check_errors(input_data)
            if error_status == 0:
                st.error(f"Error: {error_message}")
                return

            response = requests.post(L1_SAMPLE_SIZE_ENDPOINT, json=input_data)
            
            if response.status_code == 200:
                result = response.json()
                st.success(f"L1 Sample Size: {result['value']}")
                st.info(result['message'])
            else:
                st.error(f"Error: {response.json()['detail']}")

    def l2_sample_size_calculator():
        st.subheader("L2 Sample Size Calculator")
        
        # Input fields
        total_samples = st.number_input("Total number of samples: The total number of data points that third party will sample (typically between 100-1000). Range > 0", min_value=1, value=100)
        average_truth_score = st.slider("Average truth score: The expected average truth score across all blocks (typically between 0.2-0.5). Ideally, should be based on some real data from the sector in question. Higher is worse (i.e. more mismatches between subordinate and 3P). 0 < Range < 1", min_value=0.0, max_value=1.0, value=0.5)
        variance_across_blocks = st.slider("Variance across blocks: The expected standard deviation of mean truth score across blocks (typically between 0.1-0.5). Ideally, should be based on some real data from the sector in question. The higher this value, the easier it will be to correctly rank the blocks. Range > 0", min_value=0.0, max_value=1.0, value=0.1)
        variance_within_block = st.slider("Variance within block: The expected standard deviation across subordinates within a block (typically between 0.1-0.5). Ideally, should be based on some real data from the sector in question. The higher this value, the more difficult it will be to correctly rank the blocks. Range > 0", min_value=0.0, max_value=1.0, value=0.1)
        level_test = st.selectbox("Level of test: The aggregation level at which 3P will test and give reward/punishment.", ["Block", "District", "State"])
        n_subs_per_block = st.number_input("Number of subordinates per block: The number of subordinates in a block. Range > 1", min_value=1, value=10)
        n_blocks_per_district = st.number_input("Number of blocks per district: The number of blocks in a district. Range >= 1", min_value=1, value=5)
        n_district = st.number_input("Number of districts: Number of districts. Range >= 1", min_value=1, value=1)
        n_simulations = st.number_input("Number of simulations: By default, this should be set to 100. The number of times the algorithm will be run to estimate the number of samples required. Higher n_simulations will give a more accurate answer, but will take longer to run. Range > 1", min_value=1, value=100)
        min_sub_per_block = st.number_input("Minimum subordinates per block: Minimum number of subordinates to be measured in each block. By default, this should be set to 1. 0 < Range < n_sub_per_block", min_value=1, value=1)

        if st.button("Calculate L2 Sample Size"):
            input_data = {
                "total_samples": total_samples,
                "average_truth_score": average_truth_score,
                "variance_across_blocks": variance_across_blocks,
                "variance_within_block": variance_within_block,
                "level_test": level_test,
                "n_subs_per_block": n_subs_per_block,
                "n_blocks_per_district": n_blocks_per_district,
                "n_district": n_district,
                "n_simulations": n_simulations,
                "min_sub_per_block": min_sub_per_block
            }
            
            # Error handling
            error_status, error_message = check_errors(input_data)
            if error_status == 0:
                st.error(f"Error: {error_message}")
                return

            response = requests.post(L2_SAMPLE_SIZE_ENDPOINT, json=input_data)
            
            if response.status_code == 200:
                result = response.json()
                st.success(f"L2 Sample Size: {result['value']['n_samples']}")
                st.info(result['message'])
                
                # Create plot
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=list(range(len(result['value']['true_disc']))), y=result['value']['true_disc'], mode='lines', name='True Discrepancy'))
                fig.add_trace(go.Scatter(x=list(range(len(result['value']['meas_disc']))), y=result['value']['meas_disc'], mode='markers', name='Measured Discrepancy'))
                fig.update_layout(
                    title="True vs Measured Discrepancy",
                    xaxis_title=f"{level_test} Index",
                    yaxis_title="Discrepancy Score"
                )
                st.plotly_chart(fig)
            else:
                st.error(f"Error: {response.json()['detail']}")

    def third_party_sampling_strategy():
        st.subheader("3P Sampling Strategy Predictor")
        
        # Input fields
        total_samples = st.number_input("Total number of samples: The total number of data points that third party will sample (typically between 100-1000). Range > 0", min_value=1, value=100)
        average_truth_score = st.slider("Average truth score: The expected average truth score across all blocks (typically between 0.2-0.5). Ideally, should be based on some real data from the sector in question. Higher is worse (i.e. more mismatches between subordinate and 3P). 0 < Range < 1", min_value=0.0, max_value=1.0, value=0.5)
        variance_across_blocks = st.slider("Variance across blocks: The expected standard deviation of mean truth score across blocks (typically between 0.1-0.5). Ideally, should be based on some real data from the sector in question. The higher this value, the easier it will be to correctly rank the blocks. Range > 0", min_value=0.0, max_value=1.0, value=0.1)
        variance_within_block = st.slider("Variance within block: The expected standard deviation across subordinates within a block (typically between 0.1-0.5). Ideally, should be based on some real data from the sector in question. The higher this value, the more difficult it will be to correctly rank the blocks. Range > 0", min_value=0.0, max_value=1.0, value=0.1)
        level_test = st.selectbox("Level of test: The aggregation level at which 3P will test and give reward/punishment.", ["Block", "District", "State"])
        n_subs_per_block = st.number_input("Number of subordinates per block: The number of subordinates in a block. Range > 1", min_value=1, value=10)
        n_blocks_per_district = st.number_input("Number of blocks per district: The number of blocks in a district. Range >= 1", min_value=1, value=5)
        n_district = st.number_input("Number of districts: Number of districts. Range >= 1", min_value=1, value=1)
        n_simulations = st.number_input("Number of simulations: By default, this should be set to 100. The number of times the algorithm will be run to estimate the number of samples required. Higher n_simulations will give a more accurate answer, but will take longer to run. Range > 1", min_value=1, value=100)
        min_sub_per_block = st.number_input("Minimum subordinates per block: Minimum number of subordinates to be measured in each block. By default, this should be set to 1. 0 < Range < n_sub_per_block", min_value=1, value=1)
        percent_blocks_plot = st.slider("Percentage of blocks to plot", min_value=0.0, max_value=100.0, value=10.0)

        if st.button("Predict 3P Sampling Strategy"):
            input_data = {
                "total_samples": total_samples,
                "average_truth_score": average_truth_score,
                "variance_across_blocks": variance_across_blocks,
                "variance_within_block": variance_within_block,
                "level_test": level_test,
                "n_subs_per_block": n_subs_per_block,
                "n_blocks_per_district": n_blocks_per_district,
                "n_district": n_district,
                "n_simulations": n_simulations,
                "min_sub_per_block": min_sub_per_block,
                "percent_blocks_plot": percent_blocks_plot
            }
            
            # Error handling
            error_status, error_message = check_errors(input_data)
            if error_status == 0:
                st.error(f"Error: {error_message}")
                return

            response = requests.post(THIRD_PARTY_SAMPLING_ENDPOINT, json=input_data)
            
            if response.status_code == 200:
                result = response.json()
                st.success("3P Sampling Strategy Prediction Complete")
                st.info(result['message'])
                
                # Display the figure
                fig = go.Figure(json.loads(result['value']['figure']))
                fig.update_layout(
                    xaxis_title="Number of Subordinates Tested per Block",
                    yaxis_title="Discrepancy Score"
                )
                st.plotly_chart(fig)
            else:
                st.error(f"Error: {response.json()['detail']}")

    # Second level dropdown for Pre-survey Analysis
    pre_survey_option = st.sidebar.selectbox("Select Pre-survey Analysis", ["L1 Sample Size Calculator", "L2 Sample Size Calculator", "3P Sampling Strategy Predictor"])
            
    if pre_survey_option == "L1 Sample Size Calculator":
        l1_sample_size_calculator()
    elif pre_survey_option == "L2 Sample Size Calculator":
        l2_sample_size_calculator()
    elif pre_survey_option == "3P Sampling Strategy Predictor":
        third_party_sampling_strategy()

# Main app
def main():
    st.sidebar.title("DiscSim Modules")
    
    # First level dropdown
    main_option = st.sidebar.selectbox("Select Module", ["Pre-survey Analysis", "Administrative Data Quality"])
    
    if main_option == "Pre-survey Analysis":
        pre_survey_analysis()
    elif main_option == "Administrative Data Quality":
        admin_data_quality_check()

if __name__ == "__main__":
    main()