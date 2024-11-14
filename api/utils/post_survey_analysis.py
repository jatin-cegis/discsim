import pandas as pd
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import seaborn as sns

def calculate_discrepancy_scores(df: pd.DataFrame, margin_of_error: float = 0.0) -> Dict[str, Any]:
    """
    Calculate discrepancy measures and composite discrepancy score for each L0 and L1 combination.
    Additionally, generate plots for these metrics.

    Args:
        df (pd.DataFrame): DataFrame containing the survey data.
        margin_of_error (float): Acceptable margin of error for measurements.

    Returns:
        Dict[str, Any]: Dictionary containing the results per L0 and L1, including plots.
    """
    
    # Ensure necessary columns are present
    required_columns = [
        'child', 'L0_height', 'L1_height', 'L0_weight', 'L1_weight', 
        'L0_id', 'L0_name', 'L1_id', 'L1_name', 
        'wasting_L0', 'stunting_L0', 'underweight_L0', 
        'wasting_L1', 'stunting_L1', 'underweight_L1'
    ]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' is missing from the data.")
    
    # Calculate discrepancies
    df['height_discrepancy_cm'] = (df['L1_height'] - df['L0_height']).abs() - margin_of_error
    df['weight_discrepancy_kg'] = (df['L1_weight'] - df['L0_weight']).abs() - margin_of_error
    
    # Clip negative discrepancies to zero
    df['height_discrepancy_cm'] = df['height_discrepancy_cm'].clip(lower=0)
    df['weight_discrepancy_kg'] = df['weight_discrepancy_kg'].clip(lower=0)
    
    # Classification accuracy metrics
    df['wasting_accuracy'] = df.apply(lambda row: 'Accurate' if row['wasting_L0'] == row['wasting_L1'] else 'Misclassified', axis=1)
    df['stunting_accuracy'] = df.apply(lambda row: 'Accurate' if row['stunting_L0'] == row['stunting_L1'] else 'Misclassified', axis=1)
    
    # Group by L0_id and L1_id
    grouped = df.groupby(['L0_id', 'L1_id'])
    
    results: List[Dict[str, Any]] = []
    
    for (l0_id, l1_id), group in grouped:
        l0_name = group['L0_name'].iloc[0]
        l1_name = group['L1_name'].iloc[0]
        
        # Discrepancy Measures
        avg_height_discrepancy = group['height_discrepancy_cm'].mean()
        avg_weight_discrepancy = group['weight_discrepancy_kg'].mean()
        
        height_discrepancy_prevalence = (group['height_discrepancy_cm'] > 0).mean() * 100
        weight_discrepancy_prevalence = (group['weight_discrepancy_kg'] > 0).mean() * 100
        
        # Measurement Accuracy
        height_accuracy = (group['height_discrepancy_cm'] <= margin_of_error).mean() * 100
        weight_accuracy = (group['weight_discrepancy_kg'] <= margin_of_error).mean() * 100
        
        # Classification Accuracy - Wasting
        wasting_acc = (group['wasting_accuracy'] == 'Accurate').mean() * 100
        wasting_mam_as_normal = group[(group['wasting_L1'].isin(['MAM', 'SAM'])) & (group['wasting_L0'] == 'Normal')].shape[0] / group.shape[0] * 100
        wasting_sam_as_mam = group[(group['wasting_L1'] == 'SAM') & (group['wasting_L0'] == 'MAM')].shape[0] / group.shape[0] * 100
        wasting_other_misclassification = 100 - (wasting_acc + wasting_mam_as_normal + wasting_sam_as_mam)
        
        # Classification Accuracy - Stunting
        stunting_acc = (group['stunting_accuracy'] == 'Accurate').mean() * 100
        stunting_mam_as_normal = group[(group['stunting_L1'].isin(['MAM', 'SAM'])) & (group['stunting_L0'] == 'Normal')].shape[0] / group.shape[0] * 100
        stunting_sam_as_mam = group[(group['stunting_L1'] == 'SAM') & (group['stunting_L0'] == 'MAM')].shape[0] / group.shape[0] * 100
        stunting_other_misclassification = 100 - (stunting_acc + stunting_mam_as_normal + stunting_sam_as_mam)
        
        # Composite Score Calculation
        # Normalize measures
        max_height_discrepancy = df['height_discrepancy_cm'].max()
        max_weight_discrepancy = df['weight_discrepancy_kg'].max()
        
        norm_height_discrepancy = avg_height_discrepancy / max_height_discrepancy if max_height_discrepancy != 0 else 0
        norm_weight_discrepancy = avg_weight_discrepancy / max_weight_discrepancy if max_weight_discrepancy != 0 else 0
        
        # Normalize prevalence percentages to [0,1]
        norm_height_discrepancy_prevalence = height_discrepancy_prevalence / 100
        norm_weight_discrepancy_prevalence = weight_discrepancy_prevalence / 100
        
        # Normalize measurement accuracies to [0,1]
        norm_height_accuracy = height_accuracy / 100
        norm_weight_accuracy = weight_accuracy / 100
        
        # Composite Score Calculation with Equal Weights
        weights = {
            'average_height_discrepancy': 1,
            'average_weight_discrepancy': 1,
            'height_discrepancy_prevalence': 1,
            'weight_discrepancy_prevalence': 1,
            'height_accuracy': 1,
            'weight_accuracy': 1
        }
        
        composite_score = (
            weights['average_height_discrepancy'] * norm_height_discrepancy +
            weights['average_weight_discrepancy'] * norm_weight_discrepancy +
            weights['height_discrepancy_prevalence'] * norm_height_discrepancy_prevalence +
            weights['weight_discrepancy_prevalence'] * norm_weight_discrepancy_prevalence +
            weights['height_accuracy'] * norm_height_accuracy +
            weights['weight_accuracy'] * norm_weight_accuracy
        )
        
        # Normalize composite score to 0-100 scale
        max_weight_sum = sum(weights.values())
        composite_score = (composite_score / max_weight_sum) * 100
        
        # Append results with casting to native Python types
        results.append({
            'L0_id': str(l0_id),  # Keep as string
            'L0_name': str(l0_name),
            'L1_id': str(l1_id),  # Keep as string
            'L1_name': str(l1_name),
            'average_height_discrepancy_cm': float(round(avg_height_discrepancy, 2)),
            'average_weight_discrepancy_kg': float(round(avg_weight_discrepancy, 2)),
            'height_discrepancy_prevalence_percent': float(round(height_discrepancy_prevalence, 2)),
            'weight_discrepancy_prevalence_percent': float(round(weight_discrepancy_prevalence, 2)),
            'height_accuracy_percent': float(round(height_accuracy, 2)),
            'weight_accuracy_percent': float(round(weight_accuracy, 2)),
            'classification_accuracy_wasting_percent': float(round(wasting_acc, 2)),
            'classification_mam_as_normal_percent': float(round(wasting_mam_as_normal, 2)),
            'classification_sam_as_mam_percent': float(round(wasting_sam_as_mam, 2)),
            'classification_other_wasting_misclassification_percent': float(round(wasting_other_misclassification, 2)),
            'classification_accuracy_stunting_percent': float(round(stunting_acc, 2)),
            'classification_mam_as_normal_stunting_percent': float(round(stunting_mam_as_normal, 2)),
            'classification_sam_as_mam_stunting_percent': float(round(stunting_sam_as_mam, 2)),
            'classification_other_stunting_misclassification_percent': float(round(stunting_other_misclassification, 2)),
            'composite_discrepancy_score': float(round(composite_score, 2))
        })
    
    # After gathering all results, generate plots
    discrepancy_df = pd.DataFrame(results)
    
    # Plot 1: Height Discrepancy (cm) vs L0
    plt.figure(figsize=(10, 6))
    sns.barplot(x='L0_name', y='average_height_discrepancy_cm', data=discrepancy_df)
    plt.title('Average Height Discrepancy (cm) per L0')
    plt.xlabel('L0 Name')
    plt.ylabel('Average Height Discrepancy (cm)')
    plt.tight_layout()
    buf_height = BytesIO()
    plt.savefig(buf_height, format='png')
    plt.close()
    plot_height = base64.b64encode(buf_height.getvalue()).decode('utf-8')
    
    # Plot 2: Weight Discrepancy (kg) vs L0
    plt.figure(figsize=(10, 6))
    sns.barplot(x='L0_name', y='average_weight_discrepancy_kg', data=discrepancy_df)
    plt.title('Average Weight Discrepancy (kg) per L0')
    plt.xlabel('L0 Name')
    plt.ylabel('Average Weight Discrepancy (kg)')
    plt.tight_layout()
    buf_weight = BytesIO()
    plt.savefig(buf_weight, format='png')
    plt.close()
    plot_weight = base64.b64encode(buf_weight.getvalue()).decode('utf-8')
    
    # Plot 3: Height Measurement Accuracy (%) vs L0
    plt.figure(figsize=(10, 6))
    sns.barplot(x='L0_name', y='height_accuracy_percent', data=discrepancy_df)
    plt.title('Height Measurement Accuracy (%) per L0')
    plt.xlabel('L0 Name')
    plt.ylabel('Height Measurement Accuracy (%)')
    plt.tight_layout()
    buf_height_acc = BytesIO()
    plt.savefig(buf_height_acc, format='png')
    plt.close()
    plot_height_acc = base64.b64encode(buf_height_acc.getvalue()).decode('utf-8')
    
    # Plot 4: Weight Measurement Accuracy (%) vs L0
    plt.figure(figsize=(10, 6))
    sns.barplot(x='L0_name', y='weight_accuracy_percent', data=discrepancy_df)
    plt.title('Weight Measurement Accuracy (%) per L0')
    plt.xlabel('L0 Name')
    plt.ylabel('Weight Measurement Accuracy (%)')
    plt.tight_layout()
    buf_weight_acc = BytesIO()
    plt.savefig(buf_weight_acc, format='png')
    plt.close()
    plot_weight_acc = base64.b64encode(buf_weight_acc.getvalue()).decode('utf-8')
    
    # Plot 5: Classification Accuracy - Wasting vs L0
    classification_wasting_df = discrepancy_df[['L0_name', 'classification_accuracy_wasting_percent', 
                                                'classification_mam_as_normal_percent', 
                                                'classification_sam_as_mam_percent', 
                                                'classification_other_wasting_misclassification_percent']]
    classification_wasting_melted = classification_wasting_df.melt(id_vars='L0_name', 
                                                                     var_name='Classification',
                                                                     value_name='Percentage')
    
    plt.figure(figsize=(12, 7))
    sns.barplot(x='L0_name', y='Percentage', hue='Classification', data=classification_wasting_melted, palette='Set2')
    plt.title('Classification Accuracy - Wasting vs L0')
    plt.xlabel('L0 Name')
    plt.ylabel('Percentage (%)')
    plt.legend(title='Classification', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    buf_class_wasting = BytesIO()
    plt.savefig(buf_class_wasting, format='png')
    plt.close()
    plot_class_wasting = base64.b64encode(buf_class_wasting.getvalue()).decode('utf-8')
    
    # Plot 6: Classification Accuracy - Stunting vs L0
    classification_stunting_df = discrepancy_df[['L0_name', 'classification_accuracy_stunting_percent', 
                                                'classification_mam_as_normal_stunting_percent', 
                                                'classification_sam_as_mam_stunting_percent', 
                                                'classification_other_stunting_misclassification_percent']]
    classification_stunting_melted = classification_stunting_df.melt(id_vars='L0_name', 
                                                                     var_name='Classification',
                                                                     value_name='Percentage')
    
    plt.figure(figsize=(12, 7))
    sns.barplot(x='L0_name', y='Percentage', hue='Classification', data=classification_stunting_melted, palette='Set3')
    plt.title('Classification Accuracy - Stunting vs L0')
    plt.xlabel('L0 Name')
    plt.ylabel('Percentage (%)')
    plt.legend(title='Classification', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    buf_class_stunting = BytesIO()
    plt.savefig(buf_class_stunting, format='png')
    plt.close()
    plot_class_stunting = base64.b64encode(buf_class_stunting.getvalue()).decode('utf-8')
    
    return {
        'grouped_discrepancy_scores': results,
        'plots': {
            'height_discrepancy_plot': plot_height,
            'weight_discrepancy_plot': plot_weight,
            'height_accuracy_plot': plot_height_acc,
            'weight_accuracy_plot': plot_weight_acc,
            'classification_wasting_plot': plot_class_wasting,
            'classification_stunting_plot': plot_class_stunting
        }
    }
