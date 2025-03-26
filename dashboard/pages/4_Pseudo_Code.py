import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from src.utils.utility_functions import set_page_config,setFooter,setheader
from src.utils.pseudo_code.helpers.file_upload import handle_file_upload
set_page_config()

API_BASE_URL = os.getenv("API_BASE_URL")
PSEUDO_CODE_ENDPOINT = f"{API_BASE_URL}/pseudo_code"
def pseudo_code_analysis():
    st.sidebar.header("Anganwadi Center Discrepancy Analysis")
    # File selection
    file_option = st.sidebar.radio(
        "Choose an option:",
        ("Upload a new file", "Select a previously uploaded file"),
    )
    uploaded_file = handle_file_upload(
        file_option, category="pseudo_code_analysis"
    )
    # Upload CSV file
    #uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        columns = df.columns.tolist()
        st.sidebar.divider()
        st.sidebar.subheader("Additional Tweaks")

        with st.form("pseodu_code"):
            # User-defined Thresholds
            red_threshold = st.sidebar.slider("Red Zone Threshold (%)", 0, 100, 30)
            green_threshold = st.sidebar.slider("Green Zone Threshold (%)", red_threshold, 100, red_threshold + 10)

            case_threshold = st.sidebar.number_input("Enter threshold for Same-to-Total Ratio", min_value=1, max_value=100, value=15)

            col1, col2 = st.columns(2,border=True)
            with col1:
                agg_level = st.selectbox("Select Aggregation Level Column", columns)
            with col2:
                discrepancy_method = st.radio("Select Discrepancy Calculation Method", ["% Mismatch Classification", "Average Difference"],horizontal=True)

            with st.expander("Preview Data"):
                st.dataframe(df.head(), use_container_width=True, hide_index=True)
            
            analyze = st.form_submit_button('Analyze')

        if analyze:
            uploaded_file.seek(0)
            files = {"file": ("uploaded_file.csv", uploaded_file, "text/csv")}
            input_data = {
                "agg_level":agg_level,
                "discrepancy_method":discrepancy_method,
                "red_threshold":red_threshold,
                "green_threshold":green_threshold,
                "case_threshold":case_threshold
            }
            with st.spinner('Analyzing... Please wait.'):
                response = requests.post(PSEUDO_CODE_ENDPOINT,files=files, data=input_data)

            if response.status_code == 200:
                status,message,data = response.json()
                if 'summary' in data:
                    a, b,c,d,e = st.columns(5)
                    a.metric("Total Sample Size", data['summary']['totalSampleSize'], border=True)
                    b.metric("Districts Covered", data['summary']['districts'], border=True)
                    c.metric("Projects Covered", data['summary']['projects'], border=True)
                    d.metric("Sectors Covered", data['summary']['sectors'], border=True)
                    e.metric("AWC Covered", data['summary']['AWC'], border=True)

                district, project, sector,awc = st.tabs(["District Level", "Project Level", "Sector Level", "AWC Level"])

                with district:
                    col1, col2 = st.columns(2)
                    with col1:
                        if 'districtLevelInsights' in data:
                            container = st.container(border=True)
                            sameHeightWeight = pd.DataFrame(data['districtLevelInsights']['sameHeightWeight'])
                            container.markdown("<h6 style='text-align:center'>Cases with Exact Same Height and Weight Measurements", unsafe_allow_html=True)
                            fig_same_values = px.bar(sameHeightWeight, x="Metric", y="Percentage (%)", color="Metric", text="Percentage (%)",color_discrete_map = {'Exact same height': '#4285f4', 'Exact same weight': '#34a853'})
                            fig_same_values.update_layout(showlegend=False,margin=dict(t=0, b=0),height=300,xaxis_title=None,yaxis_title="% Remeasurements")
                            container.plotly_chart(fig_same_values)
                            with container.expander("Show Data"):
                                st.dataframe(sameHeightWeight,hide_index=True,use_container_width=True)
                    with col2:
                         if 'childrenCategory' in data['districtLevelInsights']:
                            container = st.container(border=True)
                            childrenCategory = pd.DataFrame(data['districtLevelInsights']['childrenCategory'])
                            container.markdown("<h6 style='text-align:center'>Average Difference in Height & Weight Measurement", unsafe_allow_html=True)
                            fig_combined = px.bar(
                                childrenCategory.melt(id_vars=['Category'], value_vars=['Average Height Difference (cms)', 'Average Weight Difference (kgs)'], var_name='Metric', value_name='Value'),
                                x='Category', y='Value', color='Metric', text="Value", barmode='group',color_discrete_map = {'Average Height Difference (cms)': '#4285f4', 'Average Weight Difference (kgs)': '#34a853'}
                            )
                            fig_combined.update_traces(width=0.1)
                            fig_combined.update_layout(
                                barcornerradius=5,
                                legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
                                margin=dict(t=0, b=0),
                                height=300,
                                xaxis_title=None,
                                yaxis_title=None,
                                barmode='group',
                                bargroupgap=0.1,
                                transition={'duration': 1000, 'easing': 'cubic-in-out'}
                            )
                            container.plotly_chart(fig_combined)
                            with container.expander("Show Data"):
                                st.dataframe(childrenCategory,hide_index=True,use_container_width=True)

                    st.markdown("<h4 style='text-align:center;background-color:#34a853;color:white;margin-bottom:10px;border-radius:10px'>WASTING [WEIGHT-FOR-HEIGHT]", unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    with col1:
                       if 'wastingLevels' in data['districtLevelInsights']:
                            container = st.container(border=True)
                            wastingLevel = pd.DataFrame(data['districtLevelInsights']['wastingLevels'])
                            container.markdown("<h6 style='text-align:center'>Difference in Wasting levels between AWTs and Supervisors", unsafe_allow_html=True)
                            fig_wasting_metrics = px.bar(wastingLevel, x="Metric", y="Percentage (%)", color="Metric", text="Percentage (%)",color_discrete_map = {'AWT SAM': '#1a73e8', 'Supervisor SAM': '#0b5394', 'AWT Wasting': '#e06666', 'Supervisor Wasting': '#cc0000'})
                            fig_wasting_metrics.update_layout(showlegend=False,margin=dict(t=0, b=0),height=300,xaxis_title=None,yaxis_title="% Remeasurements")
                            container.plotly_chart(fig_wasting_metrics)
                            with container.expander("Show Data"):
                                st.dataframe(wastingLevel,hide_index=True,use_container_width=True)

                    with col2:
                       if 'wastingClassification' in data['districtLevelInsights']:
                            container = st.container(border=True)
                            wastingClassification = pd.DataFrame(data['districtLevelInsights']['wastingClassification'])
                            container.markdown("<h6 style='text-align:center'>Difference in Wasting Classification between AWTs and Supervisors", unsafe_allow_html=True)
                            fig_wasting_metrics = px.bar(wastingClassification, y="Metric", x="Percentage (%)", color="Metric", text="Percentage (%)",color_discrete_map = {'AWT Normal; Sup SAM': '#990000', 'AWT Normal; SUP MAM': '#cc0000', 'AWT MAM; SUP SAM': '#e06666', 'Other Misclassifications': '#fbbc04', 'Same Classification': '#34a853'},orientation='h')
                            fig_wasting_metrics.update_layout(showlegend=False,margin=dict(t=0, b=0),height=300,yaxis_title=None,xaxis_title=None)
                            container.plotly_chart(fig_wasting_metrics)
                            with container.expander("Show Data"):
                                st.dataframe(wastingClassification,hide_index=True,use_container_width=True)

                    st.markdown("<h4 style='text-align:center;background-color:#34a853;color:white;margin-bottom:10px;border-radius:10px'>UNDERWEIGHT [WEIGHT-FOR-AGE]", unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    with col1:
                       if 'underweightLevels' in data['districtLevelInsights']:
                            container = st.container(border=True)
                            underweightLevels = pd.DataFrame(data['districtLevelInsights']['underweightLevels'])
                            container.markdown("<h6 style='text-align:center'>Difference in Underweight levels between AWTs and Supervisors", unsafe_allow_html=True)
                            fig_underweight_metrics = px.bar(underweightLevels, x="Metric", y="Percentage (%)", color="Metric", text="Percentage (%)",color_discrete_map = {'AWT SUW': '#1a73e8', 'Supervisor SUW': '#0b5394', 'AWT UW': '#e06666', 'Supervisor UW': '#cc0000'})
                            fig_underweight_metrics.update_layout(showlegend=False,margin=dict(t=0, b=0),height=300,xaxis_title=None,yaxis_title="% Remeasurements")
                            container.plotly_chart(fig_underweight_metrics)
                            with container.expander("Show Data"):
                                st.dataframe(underweightLevels,hide_index=True,use_container_width=True)

                    with col2:
                       if 'underweightClassification' in data['districtLevelInsights']:
                            container = st.container(border=True)
                            underweightClassification = pd.DataFrame(data['districtLevelInsights']['underweightClassification'])
                            container.markdown("<h6 style='text-align:center'>Difference in Underweight Classification between AWTs and Supervisors", unsafe_allow_html=True)
                            fig_underweight_metrics = px.bar(underweightClassification, y="Metric", x="Percentage (%)", color="Metric", text="Percentage (%)",color_discrete_map = {'AWT Normal; Supervisor SUW': '#990000', 'AWT Normal; Supervisor MUW': '#e06666', 'Other Misclassifications': '#fbbc04', 'Same Classification': '#34a853'},orientation='h')
                            fig_underweight_metrics.update_layout(showlegend=False,margin=dict(t=0, b=0),height=300,yaxis_title=None,xaxis_title=None)
                            container.plotly_chart(fig_underweight_metrics)
                            with container.expander("Show Data"):
                                st.dataframe(underweightClassification,hide_index=True,use_container_width=True)

                    st.markdown("<h4 style='text-align:center;background-color:#34a853;color:white;margin-bottom:10px;border-radius:10px'>STUNTING [HEIGHT FOR AGE]", unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    with col1:
                       if 'stuntingLevels' in data['districtLevelInsights']:
                            container = st.container(border=True)
                            stuntingLevels = pd.DataFrame(data['districtLevelInsights']['stuntingLevels'])
                            container.markdown("<h6 style='text-align:center'>Difference in Stunting levels between AWTs and Supervisors", unsafe_allow_html=True)
                            fig_underweight_metrics = px.bar(stuntingLevels, x="Metric", y="Percentage (%)", color="Metric", text="Percentage (%)",color_discrete_map = {'AWT SAM': '#1a73e8', 'Supervisor SAM': '#0b5394', 'AWT Stunting': '#e06666', 'Supervisor Stunting': '#cc0000'})
                            fig_underweight_metrics.update_layout(showlegend=False,margin=dict(t=0, b=0),height=300,xaxis_title=None,yaxis_title="% Remeasurements")
                            container.plotly_chart(fig_underweight_metrics)
                            with container.expander("Show Data"):
                                st.dataframe(stuntingLevels,hide_index=True,use_container_width=True)

                    with col2:
                       if 'stuntingClassification' in data['districtLevelInsights']:
                            container = st.container(border=True)
                            stuntingClassification = pd.DataFrame(data['districtLevelInsights']['stuntingClassification'])
                            container.markdown("<h6 style='text-align:center'>Difference in Stunting classification between AWTs and Supervisors", unsafe_allow_html=True)
                            fig_underweight_metrics = px.bar(stuntingClassification, y="Metric", x="Percentage (%)", color="Metric", text="Percentage (%)",color_discrete_map = {'AWT Normal; Supervisor SAM': '#990000', 'AWT Normal; Supervisor MAM': '#e06666', 'Other Misclassifications': '#fbbc04', 'Same Classifications': '#34a853'},orientation='h')
                            fig_underweight_metrics.update_layout(showlegend=False,margin=dict(t=0, b=0),height=300,yaxis_title=None,xaxis_title=None)
                            container.plotly_chart(fig_underweight_metrics)
                            with container.expander("Show Data"):
                                st.dataframe(stuntingClassification,hide_index=True,use_container_width=True)


                with project:
                    st.warning("Project Level")
                with sector:
                    st.warning("Sector Level")
                with awc:
                    st.warning("AWC Level")
                            
            else:
                st.error(f"Error: {response.json()['detail']}")
    
    
    else:
        st.info("Please upload a CSV file to begin.")

if __name__ == "__main__":
    selectedNav = setheader("Pseudo Code")
    if selectedNav == "Pre Survey":
          st.switch_page("pages/1_Pre_Survey.py")
    if selectedNav == "Admin Data Quality":
          st.switch_page("pages/2_Admin_Data_Quality_Checklist.py")
    if selectedNav == "Post Survey":
          st.switch_page("pages/3_Post_Survey.py")
    pseudo_code_analysis()

    setFooter()
