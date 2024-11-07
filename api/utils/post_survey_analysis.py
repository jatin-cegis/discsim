import pandas as pd
from typing import Dict, Any

def calculate_discrepancy_scores(df: pd.DataFrame, margin_of_error: float = 0.0) -> Dict[str, Any]:
    """
    Calculate discrepancy measures and composite discrepancy score.

    Args:
        df (pd.DataFrame): DataFrame containing the survey data.
        margin_of_error (float): Acceptable margin of error for measurements.

    Returns:
        Dict[str, Any]: Dictionary containing the results.
    """

    # Ensure necessary columns are present
    required_columns = ['child', 'L0_height', 'L1_height', 'L0_weight', 'L1_weight']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' is missing from the data.")

    # Discrepancy Measures
    df['height_discrepancy'] = (df['L1_height'] - df['L0_height']).abs() - margin_of_error
    df['weight_discrepancy'] = (df['L1_weight'] - df['L0_weight']).abs() - margin_of_error

    # Ensure discrepancies are not negative after subtracting margin of error
    df['height_discrepancy'] = df['height_discrepancy'].clip(lower=0)
    df['weight_discrepancy'] = df['weight_discrepancy'].clip(lower=0)

    # Discrepancy Prevalence
    height_discrepancy_prevalence = (df['height_discrepancy'] > 0).mean() * 100
    weight_discrepancy_prevalence = (df['weight_discrepancy'] > 0).mean() * 100

    # Composite Discrepancy Score
    # Normalize measures and assign weights
    # For simplicity, assign equal weights to all measures
    weights = {
        'average_height_discrepancy': 1,
        'average_weight_discrepancy': 1,
        'height_discrepancy_prevalence': 1,
        'weight_discrepancy_prevalence': 1
    }

    # Normalize measures
    max_height_discrepancy = df['height_discrepancy'].max()
    max_weight_discrepancy = df['weight_discrepancy'].max()

    # Avoid division by zero
    norm_height_discrepancy = df['height_discrepancy'].mean() / max_height_discrepancy if max_height_discrepancy != 0 else 0
    norm_weight_discrepancy = df['weight_discrepancy'].mean() / max_weight_discrepancy if max_weight_discrepancy != 0 else 0

    # Normalize prevalence percentages to [0,1]
    norm_height_discrepancy_prevalence = height_discrepancy_prevalence / 100
    norm_weight_discrepancy_prevalence = weight_discrepancy_prevalence / 100

    # Calculate composite score
    composite_score = (
        weights['average_height_discrepancy'] * norm_height_discrepancy +
        weights['average_weight_discrepancy'] * norm_weight_discrepancy +
        weights['height_discrepancy_prevalence'] * norm_height_discrepancy_prevalence +
        weights['weight_discrepancy_prevalence'] * norm_weight_discrepancy_prevalence
    )

    # Normalize composite score to 0-100 scale
    max_weight_sum = sum(weights.values())
    composite_score = (composite_score / max_weight_sum) * 100

    result = {
        'discrepancy_measures': {
            'average_height_discrepancy': df['height_discrepancy'].mean(),
            'average_weight_discrepancy': df['weight_discrepancy'].mean(),
        },
        'discrepancy_prevalence': {
            'height_discrepancy_prevalence': height_discrepancy_prevalence,
            'weight_discrepancy_prevalence': weight_discrepancy_prevalence,
        },
        'composite_discrepancy_score': composite_score
    }

    return result
