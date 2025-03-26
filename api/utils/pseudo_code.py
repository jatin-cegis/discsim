import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import base64

def error_handling(params):
    return (1, "Success")
    

def anganwadi_center_data_anaylsis(file: pd.DataFrame, agg_level, disc_method, red_threshold, green_threshold, same_total_ratio):
    df = file
    required_columns = [
        'Id', 
        'Status_Wasting', 'Sup_Status_Wasting', 
        'Status_UW', 'Sup_Status_UW', 
        'Height', 'Sup_Height', 
        'Weight', 'Sup_Weight', 
        'Muac', 'Sup_Muac', 
        'AWC_ID', 'Sec_ID', 'Proj_Name', 'D_Name'
    ]
    
    for col in required_columns:
        if col not in df.columns:
            return (0, f"Error: Required column '{col}' is missing from the data.")
        
    response = {
        "agg":agg_level,
        "disc":disc_method,
        "red":red_threshold,
        "green":green_threshold,
        "same-to-total":same_total_ratio
    }

    # Mismatch Classification Conditions
    df['AWT_Normal_Sup_SAM'] = ((df['Sup_Status_Wasting'] == "SAM") & (df['Status_Wasting'] == "Normal")) * 1
    df['AWT_Normal_Sup_MAM'] = ((df['Sup_Status_Wasting'] == "MAM") & (df['Status_Wasting'] == "Normal")) * 1
    df['AWT_MAM_Sup_SAM'] = ((df['Sup_Status_Wasting'] == "SAM") & (df['Status_Wasting'] == "MAM")) * 1
    df['AWT_Normal_Sup_SUW'] = ((df['Sup_Status_UW'] == "SUW") & (df['Status_UW'] == "Normal")) * 1
    df['AWT_Normal_Sup_MUW'] = ((df['Sup_Status_UW'] == "MUW") & (df['Status_UW'] == "Normal")) * 1
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

    #Sample Size
    num_remeasurements = df.shape[0]

    #Exact Same Height and Weight - AW and Supervisor
    same_values_data = {
        "Metric": ["Exact same height", "Exact same weight"],
        "Value": [
            (df['Height'] == df['Sup_Height']).sum(),
            (df['Weight'] == df['Sup_Weight']).sum()
        ]
    }
    same_values_df = pd.DataFrame(same_values_data)
    same_values_df['Percentage (%)'] = round((same_values_df['Value'] / num_remeasurements) * 100, 1)

    #Children Classifications
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
    
    #Wasting Levels
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
    wasting_metrics_df['Percentage (%)'] = round((wasting_metrics_df['Value'] / num_remeasurements) * 100, 1)

    #Wasting Classifications
    misclassification_wasting_data = {
        "Metric": ["AWT Normal; Sup SAM", "AWT Normal; SUP MAM", "AWT MAM; SUP SAM", "Other Misclassifications", "Same Classification"],
        "Value": [
            df['AWT_Normal_Sup_SAM'].sum(),
            df['AWT_Normal_Sup_MAM'].sum(),
            df['AWT_MAM_Sup_SAM'].sum(),
            df['AWT_Sup_Other_Misclassifications_Wasting'].sum(),
            df['AWT_Sup_Same_Wasting'].sum()
        ]
    }
    misclassification_wasting_df = pd.DataFrame(misclassification_wasting_data)
    misclassification_wasting_df['Percentage (%)'] = round((misclassification_wasting_df['Value'] / num_remeasurements) * 100, 1)
    
    #UnderWeight Levels
    underweight_metrics_data = {
        "Metric": ["AWT SUW", "Supervisor SUW", "AWT UW", "Supervisor UW"],
        "Value": [
            df['Status_UW'].eq('SUW').sum(),
            df['Sup_Status_UW'].eq('SUW').sum(),
            df['AWT_Underweight'].sum(),
            df['Supervisor_Underweight'].sum()
        ]
    }
    underweight_metrics_df = pd.DataFrame(underweight_metrics_data)
    underweight_metrics_df['Percentage (%)'] = round((underweight_metrics_df['Value'] / num_remeasurements) * 100, 1)

    #Underweight Misclassification
    underweight_classification_data = {
        "Metric": [
            "AWT Normal; Supervisor SUW",
            "AWT Normal; Supervisor MUW",
            "Other Misclassifications", 
            "Same Classification",
        ],
        "Value": [
            df['AWT_Normal_Sup_SUW'].sum(),
            df['AWT_Normal_Sup_MUW'].sum(),
            df['AWT_Sup_Other_Misclassifications_Underweight'].sum(),
            df['AWT_Sup_Same_Underweight'].sum(),
        ]
    }
    underweight_classification_df = pd.DataFrame(underweight_classification_data)
    underweight_classification_df['Percentage (%)'] = round((underweight_classification_df['Value'] / num_remeasurements) * 100, 1)

    #Stunting Levels
    stunting_metrics_data = {
        "Metric": ["AWT SAM", "Supervisor SAM", "AWT Stunting", "Supervisor Stunting"],
        "Value": [
            df['Status_Stunting'].eq('SAM').sum(),
            df['Sup_Status_Stunting'].eq('SAM').sum(),
            df['AWT_Stunting'].sum(),
            df['Supervisor_Stunting'].sum()
        ]
    }
    stunting_metrics_df = pd.DataFrame(stunting_metrics_data)
    stunting_metrics_df['Percentage (%)'] = round((stunting_metrics_df['Value'] / num_remeasurements) * 100, 1)
    
    misclassification_stunting_data = {
        "Metric": ["AWT Normal; Supervisor SAM", "AWT Normal; Supervisor MAM", "Other Misclassifications", "Same Classifications"],
        "Value": [
            df['AWT_Normal_Sup_Stunt_SAM'].sum(),
            df['AWT_Normal_Sup_Stunt_MAM'].sum(),
            df['AWT_Sup_Other_Misclassifications_Stunting'].sum(),
            df['AWT_Sup_Same_Stunting'].sum()
        ]
    }
    misclassification_stunting_df = pd.DataFrame(misclassification_stunting_data)
    misclassification_stunting_df['Percentage (%)'] = round((misclassification_stunting_df['Value'] / num_remeasurements) * 100, 1)

    response_data = {
        "summary":{
            "totalSampleSize":num_remeasurements,
            "AWC": df['AWC_ID'].nunique(),
            "sectors":df['Sec_ID'].nunique(),
            "projects":df['Proj_Name'].nunique(),
            "districts":df['D_Name'].nunique()
        },
        "districtLevelInsights":{
            "sameHeightWeight":same_values_df.to_dict(orient="records"),
            "childrenCategory":children_category_data.to_dict(orient="records"),
            "wastingLevels":wasting_metrics_df.to_dict(orient="records"),
            "wastingClassification":misclassification_wasting_df.to_dict(orient="records"),
            "underweightLevels":underweight_metrics_df.to_dict(orient="records"),
            "underweightClassification":underweight_classification_df.to_dict(orient="records"),
            "stuntingLevels":stunting_metrics_df.to_dict(orient="records"),
            "stuntingClassification":misclassification_stunting_df.to_dict(orient="records")
        }
    }
    
    return (1, "Success",response_data)
