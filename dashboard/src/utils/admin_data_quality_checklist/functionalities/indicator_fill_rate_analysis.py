import json
import os
import sys
import traceback
import streamlit as st
import pandas as pd
import requests
from dotenv import load_dotenv
from src.utils.admin_data_quality_checklist.helpers.graph_functions import plot_100_stacked_bar_chart, plot_pie_chart

load_dotenv()

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE_URL = os.getenv("API_BASE_URL")

INDICATOR_FILL_RATE_ENDPOINT = f"{API_BASE_URL}/indicator_fill_rate"

def indicator_fill_rate_analysis(uploaded_file, df):
    st.session_state.drop_export_rows_complete = False
    st.session_state.drop_export_entries_complete = False
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
                                    st.dataframe(category_df, use_container_width=True, hide_index=True)
                                else:
                                    st.write(f"No {category} data found.")
                        else:
                            for category in ["missing", "invalid", "valid"]:
                                if data[category]:
                                    st.write(f"{category.capitalize()} data (up to 10 rows):")
                                    category_df = pd.DataFrame(data[category])
                                    st.dataframe(category_df, use_container_width=True, hide_index=True)
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
                            st.dataframe(analysis_df, use_container_width=True, hide_index=True)
                            display_detailed_data(result["detailed_data"][group])
                            st.write("---")
                    else:
                        st.write("Indicator Fill Rate:")
                        analysis_df = pd.DataFrame(result["analysis"])
                        st.dataframe(analysis_df, use_container_width=True, hide_index=True)
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