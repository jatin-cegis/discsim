import json
import numpy as np
from scipy.stats import binom
import matplotlib.pyplot as plt
import base64
import plotly.graph_objects as go
from mpl_toolkits.axes_grid1 import make_axes_locatable
from io import BytesIO

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
    Calculate the number of subjects and blocks based on the level of testing.

    Args:
    level_test (str): The level at which the test is being conducted ('Block', 'District', or 'State').
    n_subs_per_block (int): Number of subjects per block.
    n_blocks_per_district (int): Number of blocks per district.
    n_district (int): Number of districts.

    Returns:
    tuple: A tuple containing the number of subjects and the number of blocks.
    """
    if level_test == 'Block':
        return n_subs_per_block, n_blocks_per_district
    elif level_test == 'District':
        return n_subs_per_block * n_blocks_per_district, n_district
    elif level_test == 'State':
        return n_subs_per_block * n_blocks_per_district * n_district, 1
    else:
        print('\'level test\' should be either \'Block\' or \'District\' or \'State\'')
        return None, None

def get_real_ts(n_blocks, average_truth_score, variance_across_blocks, n_sub_per_block, variance_within_block):
    block_mean_ts = generate_true_disc(n_blocks, 0, 1, average_truth_score, variance_across_blocks, 'normal')
    real_order = list(np.argsort(block_mean_ts))
    real_ts = [generate_true_disc(n_sub_per_block, 0, 1, block_mean_ts[block], variance_within_block, 'normal') for block in range(n_blocks)]
    return real_order, real_ts

def get_list_n_sub(n_sub_per_block, min_sub_per_block):
    return list(range(min_sub_per_block, n_sub_per_block + 1))

def get_list_n_samples(total_samples, n_blocks, list_n_sub):
    return [int(total_samples/(n_blocks*n_sub)) for n_sub in list_n_sub]

def get_meas_ts(n_blocks, n_sub_per_block, n_sub_test, n_samples, real_ts, random_state):
    meas_ts = np.zeros(n_blocks)
    for block in range(n_blocks):
        subs_test = np.random.choice(list(range(n_sub_per_block)), size=n_sub_test)
        meas_ts[block] = np.mean([binom.rvs(n_samples, real_ts[block][sub], random_state=random_state)/n_samples for sub in subs_test])
    return meas_ts

def make_plot(meas_order, list_n_sub, list_n_samples, n_blocks, percent_blocks_plot):
    fig, ax1 = plt.subplots(figsize=[10, 8])
    n_cond = len(list_n_sub)
    n_blocks_plot = max(1, int(n_blocks * percent_blocks_plot / 100))
    colors = plt.cm.Reds(np.linspace(0.3, 1, n_blocks_plot))

    mean_rank = np.zeros([n_blocks_plot, n_cond])
    std_rank = np.zeros([n_blocks_plot, n_cond])
    for block in range(n_blocks_plot):
        mean_rank[block, :] = np.array([n_blocks - np.mean(meas_order[i][block, :] + 1) for i in range(n_cond)])
        std_rank[block, :] = np.array([np.std(meas_order[i][block, :]) for i in range(n_cond)])
        ax1.errorbar(list_n_sub, mean_rank[block, :], std_rank[block, :],
                     color=colors[block], marker='o', elinewidth=0.5, capsize=2,
                     label=f'Real rank of unit with measured rank = {n_blocks - block}')

    ax1.plot(list_n_sub, np.ones(n_cond)*n_blocks, color='b', linestyle='--', linewidth=1.5, label='Highest possible rank (k)')
    ax1.legend(fontsize=14)
    ax1.set_xticks(list_n_sub)
    ax1.set_xlabel('Number of L0s (m) per block tested by supervisor', fontsize=14)
    ax1.set_ylabel('Real rank of blocks with\nthe best measured truth scores', fontsize=14)
    ax1.set_ylim([0, n_blocks + 1])

    divider = make_axes_locatable(ax1)
    ax2 = divider.append_axes("bottom", size="5%", pad=0.7)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.set_xticks(list_n_sub)
    ax2.set_xticklabels(list_n_samples)
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_xlabel('Number of samples (n) per L0', fontsize=14)
    ax2.yaxis.set_visible(False)

    return fig

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


def l1_sample_size_calculator(params):
    """
    Calculate the L1 sample size based on given parameters.

    Args:
    params (dict): A dictionary of input parameters.

    Returns:
    dict: A dictionary containing status, message, and calculated sample size.
    """
    error_status, error_message = error_handling(params)
    if error_status == 0:
        return {"status": 0, "message": error_message}

    n_sub = number_of_subs(
        params["level_test"],
        params["n_subs_per_block"],
        params["n_blocks_per_district"],
        params["n_district"],
    )
    n_punish = int(np.ceil((params["percent_punish"] / 100) * n_sub))
    n_guarantee = int(np.ceil((params["percent_guarantee"] / 100) * n_sub))

    def simulate(n_samples):
        true_disc = generate_true_disc(
            n_sub,
            params["min_disc"],
            params["max_disc"],
            params["mean_disc"],
            params["std_disc"],
            params["distribution"],
        )
        meas_disc = generate_meas_disc(true_disc, n_samples)
        worst_offenders = np.argsort(true_disc)[-n_punish:]
        punished = np.argsort(meas_disc)[-n_punish:]
        return len(set(worst_offenders) & set(punished)) >= n_guarantee

    left, right = params["min_n_samples"], params["max_n_samples"]
    while left < right:
        mid = (left + right) // 2
        success_count = sum(simulate(mid) for _ in range(params["n_simulations"]))
        if success_count / params["n_simulations"] >= params["confidence"]:
            right = mid
        else:
            left = mid + 1

    return {
        "status": 1,
        "message": f"L1 sample size calculated successfully.",
        "value": left,
    }


def l2_sample_size_calculator(params):
    """
    Calculate the L2 sample size based on given parameters.

    Args:
    params (dict): A dictionary of input parameters.

    Returns:
    dict: A dictionary containing status, message, and calculated results including true and measured discrepancies.
    """
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

    true_disc = generate_true_disc(
        n_blocks,
        0,
        1,
        params["average_truth_score"],
        params["variance_across_blocks"],
        "normal",
    )
    meas_disc = generate_meas_disc(true_disc, params["total_samples"] // n_blocks)

    return {
        "status": 1,
        "message": "L2 sample size calculated successfully.",
        "value": {
            "true_disc": true_disc.tolist(),
            "meas_disc": meas_disc.tolist(),
            "n_samples": params["total_samples"] // n_blocks,
        },
    }

def make_plot_plotly(meas_order, list_n_sub, list_n_samples, n_blocks, percent_blocks_plot):
    n_cond = len(list_n_sub)
    n_blocks_plot = max(1, int(n_blocks * percent_blocks_plot / 100))
    
    fig = go.Figure()
    
    for block in range(n_blocks_plot):
        mean_rank = np.array([n_blocks - np.mean(meas_order[i][block, :] + 1) for i in range(n_cond)])
        std_rank = np.array([np.std(meas_order[i][block, :]) for i in range(n_cond)])
        
        fig.add_trace(go.Scatter(
            x=list_n_sub,
            y=mean_rank,
            error_y=dict(type='data', array=std_rank, visible=True),
            mode='markers+lines',
            name=f'Real rank of unit with measured rank = {n_blocks - block}'
        ))
    
    fig.add_trace(go.Scatter(
        x=list_n_sub,
        y=[n_blocks] * n_cond,
        mode='lines',
        line=dict(color='blue', dash='dash'),
        name='Highest possible rank (k)'
    ))
    
    fig.update_layout(
        title='3P Sampling Strategy Prediction',
        xaxis_title='Number of L0s (m) per block tested by supervisor',
        yaxis_title='Real rank of blocks with the best measured truth scores',
        xaxis=dict(tickmode='array', tickvals=list_n_sub, ticktext=list_n_sub),
        yaxis=dict(range=[0, n_blocks + 1]),
        legend_title='Ranks',
        hovermode='closest'
    )
    
    # Add secondary x-axis for number of samples
    fig.update_layout(
        xaxis2=dict(
            overlaying='x',
            side='bottom',
            tickmode='array',
            tickvals=list_n_sub,
            ticktext=list_n_samples,
            title='Number of samples (n) per L0',
            anchor='y',
            showgrid=False
        )
    )
    
    return fig

def third_party_sampling_strategy(params):
    error_status, error_message = error_handling(params)
    if error_status == 0:
        return {"status": 0, "message": error_message}

    n_sub_per_block, n_blocks = number_of_subs(
        params["level_test"],
        params["n_subs_per_block"],
        params["n_blocks_per_district"],
        params["n_district"]
    )

    real_order, real_ts = get_real_ts(
        n_blocks,
        params["average_truth_score"],
        params["variance_across_blocks"],
        n_sub_per_block,
        params["variance_within_block"]
    )

    list_n_sub = get_list_n_sub(n_sub_per_block, params["min_sub_per_block"])
    list_n_samples = get_list_n_samples(params["total_samples"], n_blocks, list_n_sub)

    meas_order = {}
    for i, n_sub in enumerate(list_n_sub):
        n_samples = list_n_samples[i]
        meas_order[i] = np.zeros([n_blocks, params["n_simulations"]])
        
        for sim in range(params["n_simulations"]):
            meas_order[i][:, sim] = np.argsort(get_meas_ts(n_blocks, n_sub_per_block, n_sub, n_samples, real_ts, sim))

    figImg = make_plot(meas_order, list_n_sub, list_n_samples, n_blocks, params["percent_blocks_plot"])
    fig = make_plot_plotly(meas_order, list_n_sub, list_n_samples, n_blocks, params["percent_blocks_plot"])
    
    # Convert plot to base64 string
    buf = BytesIO()
    figImg.savefig(buf, format="png")
    plt.close(figImg)  # Close the figure to free up memory
    plot_data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return {
        "status": 1,
        "message": "3P Sampling Strategy calculated successfully.",
        "value": {
            "real_order": [int(x) for x in real_order],
            "meas_order": {str(k): v.tolist() for k, v in meas_order.items()},
            "list_n_sub": [int(x) for x in list_n_sub],
            "list_n_samples": [int(x) for x in list_n_samples],
            "figure": json.loads(fig.to_json()),
            "figureImg": plot_data
        },
    }