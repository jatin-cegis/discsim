import json
import numpy as np
from typing import List, Dict
import plotly.graph_objects as go
from scipy.stats import binom
import plotly

def error_handling(params):
    """
    Perform basic error checks on the input parameters.

    Args:
    params (dict): A dictionary of input parameters.

    Returns:
    tuple: A tuple containing a status code (0 for error, 1 for success) and a message.
    """
    # Basic error checks
    for key, value in params.items():
        if isinstance(value, (int, float)) and value < 0:
            return (0, f"ERROR: {key} must be non-negative")

    if "percent_punish" in params and (
        params["percent_punish"] < 0 or params["percent_punish"] > 100
    ):
        return (0, "ERROR: percent_punish must be between 0 and 100")

    if "percent_guarantee" in params and (
        params["percent_guarantee"] < 0
        or params["percent_guarantee"] > params["percent_punish"]
    ):
        return (0, "ERROR: percent_guarantee must be between 0 and percent_punish")

    if "confidence" in params and (
        params["confidence"] <= 0 or params["confidence"] >= 1
    ):
        return (0, "ERROR: confidence must be between 0 and 1")

    if "distribution" in params and params["distribution"] not in ["uniform", "normal"]:
        return (0, "ERROR: distribution must be 'uniform' or 'normal'")

    return (1, "Success")


def number_of_subs(level_test, n_subs_per_block, n_blocks_per_district, n_district):
    """
    Calculate the number of subjects based on the level of testing.

    Args:
    level_test (str): The level at which the test is being conducted ('Block', 'District', or 'State').
    n_subs_per_block (int): Number of subjects per block.
    n_blocks_per_district (int): Number of blocks per district.
    n_district (int): Number of districts.

    Returns:
    int: The total number of subjects for the given level.
    """
    if level_test == "Block":
        return n_subs_per_block
    elif level_test == "District":
        return n_subs_per_block * n_blocks_per_district
    elif level_test == "State":
        return n_subs_per_block * n_blocks_per_district * n_district


def generate_true_disc(n, min_disc, max_disc, mean_disc, std_disc, distribution):
    """
    Generate true discrepancy values based on the specified distribution.

    Args:
    n (int): Number of values to generate.
    min_disc (float): Minimum discrepancy value.
    max_disc (float): Maximum discrepancy value.
    mean_disc (float): Mean discrepancy value (for normal distribution).
    std_disc (float): Standard deviation of discrepancy (for normal distribution).
    distribution (str): Type of distribution ('uniform' or 'normal').

    Returns:
    numpy.array: Array of generated discrepancy values.
    """
    if distribution == "uniform":
        return np.random.uniform(min_disc, max_disc, n)
    elif distribution == "normal":
        disc = np.random.normal(mean_disc, std_disc, n)
        return np.clip(disc, min_disc, max_disc)


def generate_meas_disc(true_disc, n_samples):
    """
    Generate measured discrepancy values based on true discrepancy.

    Args:
    true_disc (numpy.array): Array of true discrepancy values.
    n_samples (int): Number of samples per measurement.

    Returns:
    numpy.array: Array of measured discrepancy values.
    """
    return np.array([binom.rvs(n_samples, td) / n_samples for td in true_disc])


# def l1_sample_size_calculator(params):
#     """
#     Calculate the L1 sample size based on given parameters.

#     Args:
#     params (dict): A dictionary of input parameters.

#     Returns:
#     dict: A dictionary containing status, message, and calculated sample size.
#     """
#     error_status, error_message = error_handling(params)
#     if error_status == 0:
#         return {"status": 0, "message": error_message}

#     n_sub = number_of_subs(
#         params["level_test"],
#         params["n_subs_per_block"],
#         params["n_blocks_per_district"],
#         params["n_district"],
#     )
#     n_punish = int(np.ceil((params["percent_punish"] / 100) * n_sub))
#     n_guarantee = int(np.ceil((params["percent_guarantee"] / 100) * n_sub))

#     def simulate(n_samples):
#         true_disc = generate_true_disc(
#             n_sub,
#             params["min_disc"],
#             params["max_disc"],
#             params["mean_disc"],
#             params["std_disc"],
#             params["distribution"],
#         )
#         meas_disc = generate_meas_disc(true_disc, n_samples)
#         worst_offenders = np.argsort(true_disc)[-n_punish:]
#         punished = np.argsort(meas_disc)[-n_punish:]
#         return len(set(worst_offenders) & set(punished)) >= n_guarantee

#     left, right = params["min_n_samples"], params["max_n_samples"]
#     while left < right:
#         mid = (left + right) // 2
#         success_count = sum(simulate(mid) for _ in range(params["n_simulations"]))
#         if success_count / params["n_simulations"] >= params["confidence"]:
#             right = mid
#         else:
#             left = mid + 1

#     return {
#         "status": 1,
#         "message": f"L1 sample size calculated successfully.",
#         "value": left,
#     }


# def l2_sample_size_calculator(params):
#     """
#     Calculate the L2 sample size based on given parameters.

#     Args:
#     params (dict): A dictionary of input parameters.

#     Returns:
#     dict: A dictionary containing status, message, and calculated results including true and measured discrepancies.
#     """
#     error_status, error_message = error_handling(params)
#     if error_status == 0:
#         return {"status": 0, "message": error_message}

#     n_sub = number_of_subs(
#         params["level_test"],
#         params["n_subs_per_block"],
#         params["n_blocks_per_district"],
#         params["n_district"],
#     )
#     n_blocks = n_sub // params["n_subs_per_block"]

#     true_disc = generate_true_disc(
#         n_blocks,
#         0,
#         1,
#         params["average_truth_score"],
#         params["variance_across_blocks"],
#         "normal",
#     )
#     meas_disc = generate_meas_disc(true_disc, params["total_samples"] // n_blocks)

#     return {
#         "status": 1,
#         "message": "L2 sample size calculated successfully.",
#         "value": {
#             "true_disc": true_disc.tolist(),
#             "meas_disc": meas_disc.tolist(),
#             "n_samples": params["total_samples"] // n_blocks,
#         },
#     }


def third_party_sampling_strategy(params):
    error_status, error_message = error_handling(params)
    if error_status == 0:
        return {"status": 0, "message": error_message}

    n_sub = number_of_subs(
        params["level_test"],
        params["n_subs_per_block"],
        params["n_blocks_per_district"],
        params["n_district"],
    )
    n_blocks = n_sub // params["n_subs_per_block"]

    # Generate true discrepancy scores
    true_disc = generate_true_disc(
        n_blocks,
        0,
        1,
        params["average_truth_score"],
        params["variance_across_blocks"],
        "normal",
    )

    results = []
    for n_sub_tested in range(1, params["n_subs_per_block"] + 1):
        n_samples = params["total_samples"] // (n_blocks * n_sub_tested)
        meas_disc = np.array(
            [
                generate_meas_disc(true_disc, n_samples)
                for _ in range(params["n_simulations"])
            ]
        )
        results.append(
            {
                "n_sub_tested": n_sub_tested,
                "n_samples": n_samples,
                "meas_disc": meas_disc.tolist(),
            }
        )

    # Create box-and-whisker plot
    fig = go.Figure()
    for result in results:
        fig.add_trace(
            go.Box(
                y=np.array(result["meas_disc"]).flatten(),
                name=f"{result['n_sub_tested']} subs<br>{result['n_samples']} samples",
                boxpoints="outliers",
            )
        )

    fig.add_trace(
        go.Scatter(
            y=true_disc,
            mode="markers",
            marker=dict(color="red", size=10, symbol="star"),
            name="True Discrepancy",
        )
    )

    fig.update_layout(
        title="Measured vs True Discrepancy",
        xaxis_title="Number of Subordinates Tested per Block",
        yaxis_title="Discrepancy Score",
        boxmode="group",
    )

    return {
        "status": 1,
        "message": "3P Sampling Strategy calculated successfully.",
        "value": {
            "true_disc": true_disc.tolist(),
            "results": results,
            "figure": json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder),
        },
    }
