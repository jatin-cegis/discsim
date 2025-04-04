import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px

# Streamlit UI
st.title("Anganwadi Center Data Discrepancy Analysis")

# File Upload
st.subheader("Upload CSV Data")
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Extract column names
    columns = df.columns.tolist()
    
    # Data Validation Checks
    st.subheader("Data Validation Checks")
    
    # Unique ID Check
    uid_column = st.selectbox("Select Unique ID Column", columns)
    if df[uid_column].duplicated().any():
        st.warning("Unique ID column contains duplicates!")
    
    # Column Name Uniqueness Check
    if len(columns) != len(set(columns)):
        st.warning("There are duplicate column names in the dataset!")
    
    # Datatype Consistency Check
    dtype_issues = {col: df[col].apply(lambda x: type(x)).nunique() > 1 for col in columns}
    inconsistent_cols = [col for col, issue in dtype_issues.items() if issue]
    if inconsistent_cols:
        st.warning(f"Columns with mixed datatypes: {inconsistent_cols}")
    
    # Missing Values Check
    missing_values = df.isnull().sum()
    missing_cols = missing_values[missing_values > 0].index.tolist()
    if missing_cols:
        st.warning(f"Columns with missing values: {missing_cols}")
    
    # Aggregation Level Selection
    st.subheader("Select Aggregation Level")
    agg_level = st.selectbox("Select Aggregation Level Column", columns)
    
    # User-defined Thresholds
    st.subheader("Set Red/Green Zone Thresholds")
    red_threshold = st.slider("Red Zone Threshold (%)", 0, 100, 30)
    green_threshold = st.slider("Green Zone Threshold (%)", red_threshold, 100, red_threshold + 10)

    #threshold for case comparison
    st.subheader("Set Remeasurement Minimum Threshold")
    case_threshold = st.number_input("Enter threshold for Same-to-Total Ratio calculation", min_value=1, max_value=100, value=15)
    
    # Discrepancy Calculation Method
    st.subheader("Select Discrepancy Calculation Method")
    discrepancy_method = st.radio("Choose Method", ["% Mismatch Classification", "Average Difference"])
    
    # Wasting Mismatch
    df['AWT_Normal_Sup_SAM'] = ((df['Sup_Status_Wasting'] == "SAM") & (df['Status_Wasting'] == "Normal")) * 1
    df['AWT_Normal_Sup_MAM'] = ((df['Sup_Status_Wasting'] == "MAM") & (df['Status_Wasting'] == "Normal")) * 1
    df['AWT_MAM_Sup_SAM'] = ((df['Sup_Status_Wasting'] == "SAM") & (df['Status_Wasting'] == "MAM")) * 1

    # Underweight Mismatch
    df['AWT_Normal_Sup_SUW'] = ((df['Sup_Status_UW'] == "SUW") & (df['Status_UW'] == "Normal")) * 1
    df['AWT_Normal_Sup_MUW'] = ((df['Sup_Status_UW'] == "MUW") & (df['Status_UW'] == "Normal")) * 1

    # Addtional Height-Weight Mismatch
    df['AWT_height_eq_Sup_height'] = (df['Height'] == df['Sup_Height']) * 1
    df['AWT_weight_eq_Sup_weight'] = (df['Weight'] == df['Sup_Weight']) * 1
    
    # % Mismatch Discrepancy Condition - If any of the above conditions are true
    df['Discrepancy'] = (
        df['AWT_Normal_Sup_SAM'] | df['AWT_Normal_Sup_MAM'] | df['AWT_MAM_Sup_SAM'] |
        df['AWT_Normal_Sup_SUW'] | df['AWT_Normal_Sup_MUW'] |
        (df['AWT_height_eq_Sup_height'] == 1) | (df['AWT_weight_eq_Sup_weight'] == 1)
    )

    # Wasting Conditions
    df['AWT_Wasting'] = ((df['Status_Wasting'] == "SAM") | (df['Status_Wasting'] == "MAM")) * 1
    df['Supervisor_Wasting'] = ((df['Sup_Status_Wasting'] == "SAM") | (df['Sup_Status_Wasting'] == "MAM")) * 1
    df['AWT_Sup_Same_Wasting'] = (df['Status_Wasting'] == df['Sup_Status_Wasting']) * 1
    df['AWT_Sup_Other_Misclassifications_Wasting'] = ((df['AWT_Sup_Same_Wasting'] == 0) & (df['AWT_Normal_Sup_SAM'] == 0) & (df['AWT_Normal_Sup_MAM'] == 0) & (df['AWT_MAM_Sup_SAM'] == 0)) * 1
    
    # Underweight Conditions
    df['AWT_Underweight'] = ((df['Status_UW'] == "SUW") | (df['Status_UW'] == "MUW")) * 1
    df['Supervisor_Underweight'] = ((df['Sup_Status_UW'] == "SUW") | (df['Sup_Status_UW'] == "MUW")) * 1
    df['AWT_Sup_Same_Underweight'] = (df['Status_UW'] == df['Sup_Status_UW']) * 1
    df['AWT_Sup_Other_Misclassifications_Underweight'] = ((df['AWT_Sup_Same_Underweight'] == 0) & (df['AWT_Normal_Sup_SUW'] == 0) & (df['AWT_Normal_Sup_MUW'] == 0)) * 1

    # Date Conversions
    df['WeightDate'] = pd.to_datetime(df['WeightDate'], format='%d/%m/%Y', errors='coerce')
    df['Sup_WeightDate'] = pd.to_datetime(df['Sup_WeightDate'], format='%d/%m/%Y', errors='coerce')
    df['Gap between AWT Sup Measurements'] = (df['Sup_WeightDate'] - df['WeightDate']).dt.days

    # Stunting Conditions
    df['AWT_Stunting'] = ((df['Status_Stunting'] == 'MAM') | (df['Status_Stunting'] == 'SAM')) * 1
    df['Supervisor_Stunting'] = ((df['Sup_Status_Stunting'] == 'MAM') | (df['Sup_Status_Stunting'] == 'SAM')) * 1
    df['AWT_Normal_Sup_Stunt_SAM'] = ((df['Status_Stunting'] == 'Normal') & (df['Sup_Status_Stunting'] == 'SAM')) * 1
    df['AWT_Normal_Sup_Stunt_MAM'] = ((df['Status_Stunting'] == 'Normal') & (df['Sup_Status_Stunting'] == 'MAM')) * 1
    df['AWT_Sup_Same_Stunting'] = (df['Status_Stunting'] == df['Sup_Status_Stunting']) * 1
    df['AWT_Sup_Other_Misclassifications_Stunting'] =((df['AWT_Sup_Same_Stunting'] == 0) & (df['AWT_Normal_Sup_Stunt_MAM'] == 0) & (df['AWT_Normal_Sup_Stunt_SAM'] == 0)) * 1
    
    # Height-Weight Diff
    df['AWT_Sup_Height_Difference'] = np.round(np.where((df['Height'] != 0) & (df['Sup_Height'] != 0) & (df['Height'] != df['Sup_Height']),abs(df['Sup_Height'] - df['Height']), np.nan), 1)
    df['AWT_Sup_Weight_Difference'] = np.where((df['Weight'] != 0) & (df['Sup_Weight'] != 0) & (df['Weight'] != df['Sup_Weight']), abs(df['Weight'] - df['Sup_Weight']), np.nan)

    # Children Classifications
    df['0-3 years old'] = (df['AgeinMonthsAsDate'] < 36) * 1
    df['3-6 years old'] = np.where(df['0-3 years old'] == 0, 1, 0)

    numeric_cols = ["Height", "Weight", "Muac"]
    df['Height_Same'] = (df['Height'] == df['Sup_Height']) * 1
    df['Weight_Same'] = (df['Weight'] == df['Sup_Weight']) * 1
    df['Muac_Same'] = (df['Muac'] == df['Sup_Muac']) * 1
    for col in numeric_cols:
        df[f'{col}_Diff'] = abs(df[col] - df[f'Sup_{col}'])

    st.subheader("Preview of Updated Data")
    st.dataframe(df, use_container_width=True)

    st.subheader("Children Category Height-Weight Analysis")
    children_category_data = pd.DataFrame({
        "Category": ["0-3 years old", "3-6 years old"],
        "Count": [
            df['0-3 years old'].sum(),
            df['3-6 years old'].sum()
        ],
        "Average Height Difference (cms)": [
            round(df.loc[df['0-3 years old'] == 1, 'AWT_Sup_Height_Difference'].mean(),1),
            round(df.loc[df['3-6 years old'] == 1, 'AWT_Sup_Height_Difference'].mean(),1)
        ],
        "Average Weight Difference (kgs)": [
            round(df.loc[df['0-3 years old'] == 1, 'AWT_Sup_Weight_Difference'].mean(),1),
            round(df.loc[df['3-6 years old'] == 1, 'AWT_Sup_Weight_Difference'].mean(),1)
        ],
        "Average gap in measurement (days)": [
            round(df.loc[df['0-3 years old'] == 1, 'Gap between AWT Sup Measurements'].mean(),0),
            round(df.loc[df['3-6 years old'] == 1, 'Gap between AWT Sup Measurements'].mean(),0)
        ]
    })
    st.dataframe(children_category_data)

    # Visuals for Children Category Analysis
    fig_height = px.bar(children_category_data, x='Category', y='Average Height Difference (cms)', title='Average Height Difference by Category', color='Category')
    fig_weight = px.bar(children_category_data, x='Category', y='Average Weight Difference (kgs)', title='Average Weight Difference by Category', color='Category')
    
    st.plotly_chart(fig_height)
    st.plotly_chart(fig_weight)
    
    
    # % Mismatch Discrepancy Condition - If any of the above conditions are true
    df['Discrepancy'] = (
        df['AWT_Normal_Sup_SAM'] | df['AWT_Normal_Sup_MAM'] | df['AWT_MAM_Sup_SAM'] |
        df['AWT_Normal_Sup_SUW'] | df['AWT_Normal_Sup_MUW'] |
        (df['AWT_height_eq_Sup_height'] == 1) | (df['AWT_weight_eq_Sup_weight'] == 1)
    )

    numeric_cols = ["Height", "Weight", "Muac"]
    df['Height_Same'] = (df['Height'] == df['Sup_Height']) * 1
    df['Weight_Same'] = (df['Weight'] == df['Sup_Weight']) * 1
    df['Muac_Same'] = (df['Muac'] == df['Sup_Muac']) * 1
    for col in numeric_cols:
        df[f'{col}_Diff'] = abs(df[col] - df[f'Sup_{col}'])


        
    # Run Analysis Button
    if st.button("Analyze Data"):
        discrepancy_metrics = {}
        mismatch_counts = {}

        # Summary Table
        st.subheader("Summary Statistics")
        summary_data = {
            "Metric": ["Number of remeasurements", "Number of unique AWC visits", "Number of sectors covered", "Number of projects covered","Number of Districts covered"],
            "Value": [df.shape[0], df['AWC_ID'].nunique(), df['Sec_ID'].nunique(), df['Proj_Name'].nunique(),df['D_Name'].nunique()]
        }
        summary_df = pd.DataFrame(summary_data)
        st.table(summary_df)

        # Bar Chart for Summary Statistics
        fig_summary = px.bar(summary_df, x="Metric", y="Value", title="Summary Statistics", color="Metric", text="Value")
        st.plotly_chart(fig_summary)

         # Table for Exact Same Height & Weight
        st.subheader("Exact Same Height & Weight Table")
        same_values_data = {
            "Metric": ["Exact same height", "Exact same weight"],
            "Value": [
                (df['Height'] == df['Sup_Height']).sum(),
                (df['Weight'] == df['Sup_Weight']).sum()
            ]
        }
        same_values_df = pd.DataFrame(same_values_data)
        num_remeasurements = df.shape[0]
        same_values_df['Percentage (%)'] = round((same_values_df['Value'] / num_remeasurements) * 100, 1)
        st.table(same_values_df)
        
        # Bar Chart for Exact Same Height & Weight
        fig_same_values = px.bar(same_values_df, x="Metric", y="Percentage (%)", title="Exact Same Height & Weight Percentage", color="Metric", text="Percentage (%)")
        st.plotly_chart(fig_same_values)

        # Table for Wasting Metrics in Percentage
        st.subheader("Wasting Metrics Table (Percentage)")
        wasting_metrics_data = {
            "Metric": ["AWT SAM", "Supervisor SAM", "AWT Wasting", "Supervisor Wasting"],
            "Value": [
                df['Status_Wasting'].eq('SAM').sum(),
                df['Sup_Status_Wasting'].eq('SAM').sum(),
                df['AWT_Wasting'].sum(),
                df['Supervisor_Wasting'].sum(),
            ]
        }
        wasting_metrics_df = pd.DataFrame(wasting_metrics_data)
        wasting_metrics_df['Percentage (%)'] = round((wasting_metrics_df['Value'] / num_remeasurements) * 100, 2)
        st.table(wasting_metrics_df)
        
        # Bar Chart for Wasting Metrics
        fig_wasting_metrics = px.bar(wasting_metrics_df, x="Metric", y="Percentage (%)", title="Wasting Metrics Percentage", color="Metric", text="Percentage (%)")
        st.plotly_chart(fig_wasting_metrics)

        # Table for Misclassification Wasting in Percentage
        st.subheader("Misclassification Wasting Table (Percentage)")
        misclassification_wasting_data = {
            "Metric": ["AWT Normal; Sup SAM", "AWT Normal; SUP MAM", "AWT MAM; SUP SAM", "Other Misclassifications", "Same Classification"],
            "Value": [
                ((df['Status_Wasting'] == 'Normal') & (df['Sup_Status_Wasting'] == 'SAM')).sum(),
                ((df['Status_Wasting'] == 'Normal') & (df['Sup_Status_Wasting'] == 'MAM')).sum(),
                ((df['Status_Wasting'] == 'MAM') & (df['Sup_Status_Wasting'] == 'SAM')).sum(),
                df['AWT_Sup_Other_Misclassifications_Wasting'].sum(),
                (df['Status_Wasting'] == df['Sup_Status_Wasting']).sum()
            ]
        }
        misclassification_wasting_df = pd.DataFrame(misclassification_wasting_data)
        num_remeasurements = df.shape[0]
        misclassification_wasting_df['Percentage (%)'] = round((misclassification_wasting_df['Value'] / num_remeasurements) * 100, 1)
        st.table(misclassification_wasting_df)
        
        # Bar Chart for Misclassification Metrics
        fig_misclassification_metrics = px.bar(
            misclassification_wasting_df, 
            y="Metric", 
            x="Percentage (%)", 
            title="Misclassification Metrics Percentage", 
            color="Metric", 
            text="Percentage (%)", 
            orientation='h',
            height=400 
        )
        fig_misclassification_metrics.update_traces(marker=dict(line=dict(width=1)))  # Reduce bar width
        st.plotly_chart(fig_misclassification_metrics)

        st.subheader("AWT & Supervisor Metrics")
        underweight_classification_data = {
            "Metric": [
                "AWT Normal; Supervisor SUW",
                "AWT Normal; Supervisor MUW",
                "Other Misclassifications", 
                "Same Classification",
            ],
            "Value": [
                ((df['Status_UW'] == 'Normal') & (df['Sup_Status_UW'] == 'SUW')).sum(),
                ((df['Status_UW'] == 'Normal') & (df['Sup_Status_UW'] == 'MUW')).sum(),
                ((df['Status_UW'] != df['Sup_Status_UW']) & ~(df['Status_UW'].isin(['Normal', 'MUW', 'SUW']))).sum(),
                (df['Status_UW'] == df['Sup_Status_UW']).sum(),
            ]
        }
        underweight_classification_df = pd.DataFrame(underweight_classification_data)
        
        # Calculate percentage values based on Number of Remeasurements
        num_remeasurements = df.shape[0]
        underweight_classification_df['Percentage (%)'] = round((underweight_classification_df['Value'] / num_remeasurements) * 100, 2)
        st.dataframe(underweight_classification_df,use_container_width=True)
        
        # Bar Chart for Misclassification Metrics
        fig_misclassification_metrics = px.bar(
            underweight_classification_df, 
            y="Metric", 
            x="Percentage (%)", 
            title="Misclassification Metrics Percentage", 
            color="Metric", 
            text="Percentage (%)", 
            orientation='h',
            height=400 
        )
        fig_misclassification_metrics.update_traces(marker=dict(line=dict(width=1)))  # Reduce bar width
        st.plotly_chart(fig_misclassification_metrics)

        # Table for Underweight Metrics
        st.subheader("Underweight Metrics Table (Percentage)")
        underweight_metrics_data = {
            "Metric": ["AWT SUW", "Supervisor SUW", "AWT Underweight", "Supervisor Underweight"],
            "Value": [
                df['Status_UW'].eq('SUW').sum(),
                df['Sup_Status_UW'].eq('SUW').sum(),
                df['Status_UW'].eq('MUW').sum(),
                df['Sup_Status_UW'].eq('MUW').sum()
            ]
        }
        underweight_metrics_df = pd.DataFrame(underweight_metrics_data)
        underweight_metrics_df['Percentage (%)'] = round((underweight_metrics_df['Value'] / num_remeasurements) * 100, 2)
        st.table(underweight_metrics_df)
        
        # Bar Chart for Underweight Metrics
        fig_underweight_metrics = px.bar(
            underweight_metrics_df, 
            x="Metric", 
            y="Percentage (%)", 
            title="Underweight Metrics Percentage", 
            color="Metric", 
            text="Percentage (%)", 
            height=400
        )
        st.plotly_chart(fig_underweight_metrics)

         # Table for Stunting Metrics
        st.subheader("Stunting Metrics Table (Percentage)")
        stunting_metrics_data = {
            "Metric": ["AWT SAM", "Supervisor SAM", "AWT Stunting", "Supervisor Stunting"],
            "Value": [
                df['Status_Stunting'].eq('SAM').sum(),
                df['Sup_Status_Stunting'].eq('SAM').sum(),
                df['Status_Stunting'].eq('Stunted').sum(),
                df['Sup_Status_Stunting'].eq('Stunted').sum()
            ]
        }
        stunting_metrics_df = pd.DataFrame(stunting_metrics_data)
        num_remeasurements = df.shape[0]
        stunting_metrics_df['Percentage (%)'] = round((stunting_metrics_df['Value'] / num_remeasurements) * 100, 2)
        st.table(stunting_metrics_df)
        
        # Bar Chart for Stunting Metrics
        fig_stunting_metrics = px.bar(
            stunting_metrics_df, 
            x="Metric", 
            y="Percentage (%)", 
            title="Stunting Metrics Percentage", 
            color="Metric", 
            text="Percentage (%)", 
        )
        st.plotly_chart(fig_stunting_metrics)

        # Table for Misclassification Metrics
        st.subheader("Misclassification Metrics Table (Percentage)")
        misclassification_metrics_data = {
            "Metric": ["AWT Normal; Supervisor SAM", "AWT Normal; Supervisor MAM", "Other Misclassifications", "Same Classifications"],
            "Value": [
                ((df['Status_Stunting'] == 'Normal') & (df['Sup_Status_Stunting'] == 'SAM')).sum(),
                ((df['Status_Stunting'] == 'Normal') & (df['Sup_Status_Stunting'] == 'MAM')).sum(),
                ((df['Status_Stunting'] != df['Sup_Status_Stunting']) & ~(df['Status_Stunting'].isin(['Normal', 'MAM', 'SAM']))).sum(),
                (df['Status_Stunting'] == df['Sup_Status_Stunting']).sum()
            ]
        }
        misclassification_metrics_df = pd.DataFrame(misclassification_metrics_data)
        misclassification_metrics_df['Percentage (%)'] = round((misclassification_metrics_df['Value'] / num_remeasurements) * 100, 2)
        st.table(misclassification_metrics_df)
        
        # Bar Chart for Misclassification Metrics
        fig_misclassification_metrics = px.bar(
            misclassification_metrics_df, 
            y="Metric", 
            x="Percentage (%)", 
            title="Misclassification Metrics Percentage", 
            color="Metric", 
            text="Percentage (%)", 
            orientation='h',
            height=400
        )
        fig_misclassification_metrics.update_traces(marker=dict(line=dict(width=0.5)))
        fig_misclassification_metrics.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="right", x=1))
        st.plotly_chart(fig_misclassification_metrics)

        misclassification_table = df.groupby(agg_level).agg(
                Number_of_Remeasurements=('Discrepancy', 'count'),
                AWT_Normal_Sup_SAM=('AWT_Normal_Sup_SAM', 'sum'),
                AWT_Normal_Sup_MAM=('AWT_Normal_Sup_MAM', 'sum'),
                AWT_MAM_Sup_SAM=('AWT_MAM_Sup_SAM', 'sum'),
                Other_Misclassifications=('AWT_Sup_Other_Misclassifications_Wasting', 'sum'),
                Same_Classification=('AWT_Sup_Same_Wasting', 'sum')
            ).reset_index()
        
        # Add percentage columns by dividing each count by Number of Remeasurements
        for col in ['AWT_Normal_Sup_SAM', 'AWT_Normal_Sup_MAM', 'AWT_MAM_Sup_SAM', 'Other_Misclassifications', 'Same_Classification']:
            misclassification_table[f'{col} (%)'] = (misclassification_table[col] / misclassification_table['Number_of_Remeasurements']) * 100
            
        st.subheader("Misclassification Summary - Wasting Classification")
        st.dataframe(misclassification_table)

        misclassification_table = misclassification_table.sort_values(by=['AWT_Normal_Sup_SAM (%)', 'AWT_Normal_Sup_MAM (%)', 'AWT_MAM_Sup_SAM (%)', 'Other_Misclassifications (%)', 'Same_Classification (%)'], ascending=True)

        # First Chart for Wasting Classification
        fig, ax = plt.subplots(figsize=(10, 5))
        categories = ['AWT_Normal_Sup_SAM (%)', 'AWT_Normal_Sup_MAM (%)', 'AWT_MAM_Sup_SAM (%)', 'Other_Misclassifications (%)', 'Same_Classification (%)']
        colors = ['darkred', 'red', 'lightcoral', 'gold', 'green']
        
        bottom_vals = np.zeros(len(misclassification_table))
        for cat, color in zip(categories, colors):
            bars = ax.barh(misclassification_table[agg_level], misclassification_table[cat], left=bottom_vals, color=color, label=cat)
            for bar, val in zip(bars, misclassification_table[cat]):
                if val > 3:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2, f'{val:.1f}%', ha='center', va='center', fontsize=8, color='black')
            bottom_vals += misclassification_table[cat]
        
        ax.set_xlabel("Percentage")
        ax.set_ylabel(agg_level)
        ax.set_title("Difference between AWT and Supervisor in Wasting Classification")
        ax.legend()
        st.pyplot(fig)

        # Second Table for Underweight Classification
        st.subheader("Misclassification Summary - Underweight Classification")
        
        underweight_table = df.groupby(agg_level).agg(
            Number_of_Remeasurements=('Discrepancy', 'count'),
            AWT_Normal_Sup_SUW=('AWT_Normal_Sup_SUW', 'sum'),
            AWT_Normal_Sup_MUW=('AWT_Normal_Sup_MUW', 'sum'),
            Other_Misclassifications=('AWT_Sup_Other_Misclassifications_Underweight', 'sum'),
            Same_Classification=('AWT_Sup_Same_Underweight', 'sum')
        ).reset_index()
        
        # Add percentage columns by dividing each count by Number of Remeasurements
        for col in ['AWT_Normal_Sup_SUW', 'AWT_Normal_Sup_MUW', 'Other_Misclassifications', 'Same_Classification']:
            underweight_table[f'{col} (%)'] = (underweight_table[col] / underweight_table['Number_of_Remeasurements']) * 100

        st.dataframe(underweight_table)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        suw_muw_categories = ['AWT_Normal_Sup_SUW (%)', 'AWT_Normal_Sup_MUW (%)', 'Other_Misclassifications (%)', 'Same_Classification (%)']
        suw_muw_colors = ['darkred', 'red', 'gold', 'green']
        
        bottom_vals = np.zeros(len(underweight_table))
        for cat, color in zip(suw_muw_categories, suw_muw_colors):
            bars = ax.barh(underweight_table[agg_level], underweight_table[cat], left=bottom_vals, color=color, label=cat)
            for bar, val in zip(bars, underweight_table[cat]):
                if val > 2:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2, f'{val:.1f}%', ha='center', va='center', fontsize=10, color='black')
            bottom_vals += underweight_table[cat]
        
        ax.set_xlabel("Percentage")
        ax.set_ylabel("Project")
        ax.set_title("Difference between AWT and Supervisor in SUW/MUW Classification")
        ax.legend()
        
        st.pyplot(fig)

        # Table for AWT & Supervisor Wasting Classification
        st.subheader("AWT & Supervisor Wasting Classification Table")
        wasting_table = df.groupby(agg_level).agg(
            Number_of_Remeasurements=('Discrepancy', 'count'),
            AWT_SAM=('Status_Wasting', lambda x: (x == 'SAM').sum()),
            Supervisor_SAM=('Sup_Status_Wasting', lambda x: (x == 'SAM').sum()),
            AWT_Wasting=('AWT_Wasting', 'sum'),
            Supervisor_Wasting=('Supervisor_Wasting', 'sum')
        ).reset_index()
        # Add percentage columns by dividing each count by Number of Remeasurements
        for col in ['AWT_SAM', 'Supervisor_SAM', 'AWT_Wasting', 'Supervisor_Wasting']:
            wasting_table[f'{col} (%)'] = round((wasting_table[col] / wasting_table['Number_of_Remeasurements']) * 100)
        wasting_table['Sup-AWT (%) Difference'] = round(((wasting_table['Supervisor_Wasting'] - wasting_table['AWT_Wasting']) / wasting_table['Number_of_Remeasurements']) * 100)
        st.dataframe(wasting_table)

        fig, ax = plt.subplots(figsize=(12, 6))
        categories = ['AWT_SAM (%)', 'Supervisor_SAM (%)', 'AWT_Wasting (%)', 'Supervisor_Wasting (%)']
        colors = ['darkred', 'red', 'lightcoral', 'gold']
        x = np.arange(len(wasting_table[agg_level]))
        width = 0.2 
        # Create separate bars for each category
        for i, (cat, color) in enumerate(zip(categories, colors)):
            bars = ax.bar(x + (i - 1.5) * width, wasting_table[cat], width=width, color=color, label=cat)
            for bar, val in zip(bars, wasting_table[cat]):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{int(val)}%', ha='center', va='bottom', fontsize=8, color='black')
        ax.set_xticks(x)
        ax.set_xticklabels(wasting_table[agg_level], rotation=45, ha='right')
        ax.set_ylabel("Percentage")
        ax.set_title("AWT vs. Supervisor Wasting Classification")
        ax.legend()
        st.pyplot(fig)

        # Table for AWT & Supervisor Underweight Classification
        st.subheader("AWT & Supervisor Wasting Classification Table")
        underweight_table = df.groupby(agg_level).agg(
            Number_of_Remeasurements=('Discrepancy', 'count'),
            AWT_SUW=('Status_UW', lambda x: (x == 'SUW').sum()),
            Supervisor_SUW=('Sup_Status_UW', lambda x: (x == 'SUW').sum()),
            AWT_Underweight=('AWT_Underweight', 'sum'),
            Supervisor_Underweight=('Supervisor_Underweight', 'sum')
        ).reset_index()
        # Add percentage columns by dividing each count by Number of Remeasurements
        for col in ['AWT_SUW', 'Supervisor_SUW', 'AWT_Underweight', 'Supervisor_Underweight']:
            underweight_table[f'{col} (%)'] = round((underweight_table[col] / underweight_table['Number_of_Remeasurements']) * 100)
        underweight_table[f'Sup-AWT (%) Difference'] = round(((underweight_table['Supervisor_Underweight'] - underweight_table['AWT_Underweight']) / underweight_table['Number_of_Remeasurements']) * 100)
        st.dataframe(underweight_table)

        fig, ax = plt.subplots(figsize=(12, 6))
        categories = ['AWT_SUW (%)', 'Supervisor_SUW (%)', 'AWT_Underweight (%)', 'Supervisor_Underweight (%)']
        colors = ['darkred', 'red', 'lightcoral', 'gold']
        x = np.arange(len(underweight_table[agg_level]))
        width = 0.2 
        # Create separate bars for each category
        for i, (cat, color) in enumerate(zip(categories, colors)):
            bars = ax.bar(x + (i - 1.5) * width, underweight_table[cat], width=width, color=color, label=cat)
            for bar, val in zip(bars, underweight_table[cat]):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{int(val)}%', ha='center', va='bottom', fontsize=8, color='black')
        ax.set_xticks(x)
        ax.set_xticklabels(underweight_table[agg_level], rotation=45, ha='right')
        ax.set_ylabel("Percentage")
        ax.set_title("AWT vs. Supervisor Underweight Classification")
        ax.legend()
        st.pyplot(fig)
        
        if discrepancy_method == "% Mismatch Classification":
            discrepancy_metrics['Discrepancy Rate (%)'] = df.groupby(agg_level)['Discrepancy'].mean()*100
            mismatch_counts['Discrepancy Cases'] = df.groupby(agg_level)['Discrepancy'].sum()
        elif discrepancy_method == "Average Difference":
            for col in numeric_cols:
                discrepancy_metrics[f'{col} Avg Difference'] = df.groupby(agg_level)[f'{col}_Diff'].mean()
                discrepancy_metrics[f'Same {col}'] = df.groupby(agg_level)[f'{col}_Same'].sum()
        
        discrepancy_df = pd.DataFrame(discrepancy_metrics).reset_index()
        discrepancy_df['Number of Remeasurements'] = df.groupby(agg_level).size().values
        
        # Add mismatch case count
        for key, value in mismatch_counts.items():
            discrepancy_df[key] = value.values
        
        # Compute Percentile for Discrepancy Rate
        if discrepancy_method == "% Mismatch Classification":
            discrepancy_df['100% - Discrepancy Rate'] = 100 - discrepancy_df['Discrepancy Rate (%)']
            discrepancy_df['Percentile'] = discrepancy_df['100% - Discrepancy Rate'].apply(lambda x: np.percentile(discrepancy_df['100% - Discrepancy Rate'], x))
        elif discrepancy_method == "Average Difference":
            for col in numeric_cols:
                st.subheader(f"{col} Difference Analysis")
                diff_df = discrepancy_df[[agg_level, f'{col} Avg Difference', f'Same {col}', 'Number of Remeasurements']]
                diff_df['Same-to-Total Ratio'] = np.where(diff_df['Number of Remeasurements'] > case_threshold, (diff_df[f'Same {col}'] / diff_df['Number of Remeasurements']) * 100, np.nan)
                st.dataframe(diff_df)

                # top 12 based on Same-to-Total Ratio
                top_12 = diff_df.nlargest(12, 'Same-to-Total Ratio')

                # Visualization: Histogram for Average Difference
                fig_hist = px.bar(top_12.sort_values(by='Same-to-Total Ratio', ascending=True),
                  x='Same-to-Total Ratio', y=agg_level,
                  title=f'Top 12 {col} Same-to-Total Ratio', orientation='h')
                st.plotly_chart(fig_hist)


        if discrepancy_method == "% Mismatch Classification":
            # Assign Zones Based on Percentiles
            discrepancy_df['Zone'] = np.where(discrepancy_df['Percentile'] >= green_threshold, 'Green',np.where(discrepancy_df['Percentile'] <= red_threshold, 'Red', 'Yellow'))

            # Display Results
            st.subheader("Discrepancy Analysis Results")
            st.dataframe(discrepancy_df)

            # Visualization: Bar Chart for Discrepancy Rate
            fig_bar = px.bar(
                discrepancy_df, 
                x=agg_level, 
                y='Discrepancy Rate (%)', 
                title='Discrepancy Rate by Aggregation Level', 
                color='Discrepancy Rate (%)', 
                color_continuous_scale='Viridis' 
            )
            st.plotly_chart(fig_bar)
            
            # Visualization: Treemap for Zones
            fig_treemap = px.treemap(
                discrepancy_df, 
                path=[agg_level], 
                values='Discrepancy Rate (%)', 
                color='Zone', 
                title='Zone Distribution', 
                color_discrete_map={'Green': 'green', 'Yellow': 'yellow', 'Red': 'red'}
            )
            fig_treemap.update_layout(margin=dict(t=50, l=25, r=25, b=25))
            st.plotly_chart(fig_treemap)
