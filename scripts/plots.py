# plots.py
# Plots the data gathered from experiements

import argparse
from collections import defaultdict
import csv
from io import TextIOWrapper
import os
from pathlib import Path
from typing import Callable, Dict, List, NamedTuple
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib.typing import ColorType
from matplotlib import colormaps
import numpy as np
from datetime import timedelta
import math


class Metrics(NamedTuple):
    state: int
    metadata: int
    #redundancy: int
    t_enc: timedelta
    t_dec: timedelta


class Algorithm(NamedTuple):
    name: str
    params: dict[str, str]
    hidden: bool

    def __hash__(self) -> int:
        return hash((self.name, frozenset(self.params.items())))

Experiment = Dict[Algorithm, Dict[float, List[Metrics]]]


similarities = []
percent_formatter = ticker.PercentFormatter()
byte_formatter = ticker.EngFormatter(unit="B")
bit_formatter = ticker.EngFormatter(unit="b")
second_formatter = ticker.EngFormatter(unit="s")
algorithm_abbreviations = {
    "Baseline": "Baseline",
    "Bucketing": "Bu",
    "Rateless": "Rs",
    "Bloom+Rateless": "BlRs",
    "Bloom+Bucketing": "BlBu",
    "Bucketing+Rateless": "BuRs",
    "Bloom+Bucketing+Rateless": "BlBuRs",
    "RBloom+Rateless+Heuristic": "RbRsAn",
    "RBloom+Rateless+Similarity": "RbRsSi",
    "RBloom+Rateless+NoParams": "RbRsCo"
}


def read_algorithm(k: str) -> Algorithm:
    """
    Parses an algorithm key.
    This function assumes that the input is not malformed.
    """
    name, *params = k.replace("[", " ").replace(",", " ").removesuffix("]").split()
    formatted = {}

    for param in params:
        pname, value = param.split("=")
        if pname == "fpr":
            formatted["\\epsilon"] = value.replace("%", "\\%")
        elif pname == "lf":
            formatted["f_{ld}"] = value
        elif pname == "m":
            if math.isclose(float(value), 1 / math.log(2), rel_tol=1e-3):
                formatted["m"] = "opt"
            else:
                formatted["m"] = value
        elif pname == "angle":
            formatted["angle"] = value
        elif pname == "sim":
            formatted["sim"] = value

    return Algorithm(name, formatted, False)


def read_experiment(results_folder: str) -> Experiment:
    """
    Reads an experiment from the results folder.
    This function assumes that the input is not malformed.
    """

    exp = {}

    # Get a list of all similarity level folders
    similarity_folders = [f for f in os.listdir(results_folder) if os.path.isdir(os.path.join(results_folder, f))]

    for sim_folder in similarity_folders:
        try:
            # The folder name is the x-axis value (similarity level)
            similarity_level = float(sim_folder)
        except ValueError:
            # Skip folders that aren't floats
            continue

        similarity_path = os.path.join(results_folder, sim_folder)

        # Get all the algorithm result files in the similarity folder
        algorithm_files = [f for f in os.listdir(similarity_path) if f.endswith('.csv')]
        
        for alg_file in algorithm_files:
            # Extract the algorithm name from the filename
            algo_text = os.path.splitext(alg_file)[0]
            algo = read_algorithm(algo_text)
            if algo not in exp:
                exp[algo] = {}
            
            file_path = os.path.join(similarity_path, alg_file)
            metrics_list = []
            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                for metrics in reader:
                    try:
                        metrics_list.append(Metrics(
                            int(metrics[0]), # state
                            int(metrics[1]), # metadata
                            timedelta(microseconds=float(metrics[2])),  # t_enc
                            timedelta(microseconds=float(metrics[3])),  # t_dec
                        ))
                    except (ValueError, IndexError):
                        continue
            
            exp[algo][similarity_level] = metrics_list
            
    return exp


def fmt_label(label: Algorithm) -> str:
    """Simple label format to be displayed in legend"""

    name = algorithm_abbreviations[label.name]

    if not label.params:
        return name

    params = f'[{", ".join(f"${k} = {v}$" for k, v in label.params.items())}]'
    return f"{name} {params}"

def plot_transmitted_with_surface(exp: Experiment, colors: dict[Algorithm, ColorType], marker_dict: dict[Algorithm, str], min_similarity: int = 0, max_similarity: int = 100) -> Figure:
    """Plot only Metadata transmitted with Bloom+Rateless minimum values as a line (y-lim fixed 0 to 300kB)."""

    blra_percentages_to_plot = []

    not_hidden = filter(lambda algo: not algo.hidden, exp)
    bloom_rateless_to_show = list(filter(lambda algo: algo.name == "Bloom+Rateless" and algo.params.get('\\epsilon') in [f"{x}\\%" for x in blra_percentages_to_plot], not_hidden))
    not_hidden = filter(lambda algo: not algo.hidden, exp)
    other_algos_to_show = filter(lambda algo: algo.name != "Bloom+Rateless", not_hidden)
        
    visible_algos = list(bloom_rateless_to_show) + list(other_algos_to_show)

    fig, ax = plt.subplots(figsize=(10, 8))
    fig.subplots_adjust(left=0.20, right=0.9, top=0.9, bottom=0.25)

    ax.xaxis.set_major_formatter(percent_formatter)
    ax.yaxis.set_major_formatter(byte_formatter)
    ax.grid(linestyle="--", linewidth=0.5, alpha=0.75)
    ax.set_xlabel("Similarity", fontsize=25)
    ax.set_ylabel("Metadata", fontsize=25, labelpad=8)
    ax.tick_params(axis="both", labelsize=20)

    legend_handles = []

    # Extract Bloom+Rateless runs
    blra_runs = {
        algo: metrics for algo, metrics in exp.items()
        if not algo.hidden and algo.name == "Bloom+Rateless"
    }

    # Plot other algorithms normally
    for algo, metrics in exp.items():
        if algo.hidden or (algo.name == "Bloom+Rateless" and algo.params.get('\\epsilon') not in [f"{x}\\%" for x in blra_percentages_to_plot]):
            continue

        color = colors[algo]
        label = fmt_label(algo)
        marker = marker_dict[algo]

        if algo.name.startswith("RBloom"):
            # Use transparency, dashed line, and marker for RBloom
            line_handle, = ax.plot(similarities, [m.metadata for m in metrics], color="darkblue", lw=3, ls='--', alpha=0.7, marker=marker, markersize=5, label=label)
        else:
            line_handle, = ax.plot(similarities, [m.metadata for m in metrics], color=color, lw=2, ls='--', marker=marker, markersize=4, label=label)
        legend_handles.append(line_handle)

    if blra_runs:
        metadata_matrix = np.array([[m.metadata for m in metrics] for metrics in blra_runs.values()])
        ymin = np.min(metadata_matrix, axis=0)
        # Plot BlRa Min with solid line, marker, and increased width
        ax.plot(similarities, ymin, color="red", lw=3, ls='-', alpha=0.7, label="BlRa Min")

    ax.set_ylim(0, 255_000)

    total_legend_items = len(visible_algos) + 1  # +1 for 'BlRa Min' line

    fig.legend(
        loc="lower center",
        ncol=math.ceil(total_legend_items / 2),
        frameon=False,
        fontsize=18,
        title_fontsize=30
    )

    return fig

def plot_metric(exp: Experiment, colors: dict[Algorithm, ColorType], marker_dict: dict[Algorithm, str], line_style_dict: dict[Algorithm, str], metric_function: Callable[[Metrics],int], metric_name: str, y_formatter: ticker.EngFormatter) -> Figure:
    """Plot the result of applying metric_function to the measured metrics with multiple measurements"""
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.subplots_adjust(left=0.2, right=0.95, top=0.9, bottom=0.3)

    ax.xaxis.set_major_formatter(percent_formatter)
    ax.yaxis.set_major_formatter(y_formatter)
    ax.grid(linestyle="--", linewidth=0.5, alpha=0.75)
    ax.set_xlabel("Similarity", fontsize=25)
    ax.set_ylabel(metric_name, fontsize=25, labelpad=8)
    ax.tick_params(axis="both", labelsize=20)
    ax.set_ylim(0, 255_000)


    legend_handles = []
    for algo, metrics_by_similarity in exp.items():
        # Get sorted similarity values and corresponding lists of measurements
        similarities = sorted(metrics_by_similarity.keys())
        measurements_list = [[metric_function(m) for m in metrics_by_similarity[s]] for s in similarities]

        # Calculate mean and standard deviation for each similarity
        means = [np.mean(m) for m in measurements_list]
        stds = [np.std(m) for m in measurements_list]
        

        color = colors[algo]
        label = fmt_label(algo)
        marker = marker_dict[algo]
        line_style = line_style_dict[algo]

        line_handle, = ax.plot(similarities, means, marker=marker, linestyle=line_style, color=color, lw=2, label=label, markersize=8)
        legend_handles.append(line_handle)

        # Plot the shaded area for standard deviation
        ax.fill_between(
            similarities,
            np.array(means) - np.array(stds),
            np.array(means) + np.array(stds),
            color=color,
            alpha=0.2
        )

    # Adjust the legend to be outside the plot area
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        ncol=len(exp),
        frameon=False,
        fontsize=15,
        title_fontsize=30
    )

    return fig



def print_transmitted(exp: Experiment, what: str) -> Figure:
    """Prints the actual values of total, metadata, or redundancy transmitted (in bytes)."""
    for algo, metrics in exp.items():
        if(algo.hidden):
            continue
        label = fmt_label(algo)
        if what == "total":
            values = [m.state + m.metadata for m in metrics]
        elif what == "metadata":
            values = [m.metadata for m in metrics]
        elif what == "redundancy":
            values = [m.redundancy for m in metrics]
        else:
            raise ValueError(f"Unknown value parameter {what} for 'what'")

        formatted = [byte_formatter(v) for v in values]
        print(f"{what} {label}", " ".join(formatted), sep="\n")

def print_transmission_ratios(exp: Experiment, what: str):
    """Prints the ratios of metadata and redundancy against the total transmitted."""
    for algo, metrics in exp.items():
        if(algo.hidden):
            continue
        label = fmt_label(algo)
        total = [m.state + m.metadata for m in metrics]

        if what == "metadata":
            collected = [m.metadata for m in metrics]
        elif what == "redundancy":
            collected = [m.redundancy for m in metrics]
        else:
            raise ValueError(f"Unknown value parameter {what} for what")

        rts = [f"{m / t:.1%}" for m, t in zip(collected, total)]
        print(f"{what} {label}", " ".join(rts), sep="\n")


def plot_time_to_sync(exp: Experiment, colors: dict[Algorithm, ColorType]) -> Figure:
    """Plots the time to sync on different link configurations"""
    fig, ax = plt.subplots(layout="constrained")

    up, down = bit_formatter(exp.env.upload), bit_formatter(exp.env.download)
    ylabel = f"Time to Sync (s)\n{up}/s up, {down}/s down"

    ax.xaxis.set_major_formatter(percent_formatter)
    ax.grid(linestyle="--", linewidth=0.5, alpha=0.75)
    ax.set(xlabel="Similarity", xmargin=0, ylabel=ylabel)

    for algo, metrics in exp.items():
        if(algo.hidden):
            continue
        color = colors[algo]
        label = fmt_label(algo)
        time = [m.duration for m in metrics]
        ax.plot(similarities, time, "o-", c=color, lw=0.8, label=label)

    ax.legend(title="Algorithms")
    return fig


def main():
    """Script that extracts relevant data from logs and produces the plots for each experiment"""
    parser = argparse.ArgumentParser(prog="plots")
    parser.add_argument("files", nargs="*", default=("-"), type=argparse.FileType("r"))
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--output_data", action="store_true", help="Output the transmitted data that was input")
    parser.add_argument("--output_ratios", action="store_true", help="Output metadata and redundancy transmission ratios")
    parser.add_argument("--include", nargs="*", help="Algorithms to include")
    parser.add_argument("--exclude", nargs="*", help="Algorithms to exclude")
    parser.add_argument("--min_similarity", type=int, default=0, help="Minimum similarity to plot (default: 0)")
    parser.add_argument("--max_similarity", type=int, default=100, help="Maximum similarity to plot (default: 100)")
    args = parser.parse_args()

    include_algorithms = set(args.include) if args.include else None
    exclude_algorithms = set(args.exclude) if args.exclude else None
    
    # Set global configs for plotting
    plt.style.use("seaborn-v0_8-paper")
    plt.rc("font", family="serif")

    # Setup the out directory
    out_dir = Path("results/")
    if args.save:
        out_dir.mkdir(parents=True, exist_ok=True)

    def save_or_show(fig: Figure, fname: str):
        if args.save:
            fig.savefig(out_dir / fname, dpi=600)
            plt.close(fig)
        if args.show:
            plt.show()


    RESULTS_FOLDER = "./results" #TODO: read from args
    file = RESULTS_FOLDER
    exp = read_experiment(RESULTS_FOLDER)
        
        
    colormap = colormaps.get_cmap("tab10")
    maintain_colors:bool = True 
    #the same algorithm always has the same color, across plots with different combinations of algorithms 
            
    if maintain_colors:
        colors = {
            a: colormap(i%10)
            for i, a in enumerate(exp.keys())
        }
        line_styles = ['solid','dotted','dashdot']
        markers = ['.', 'v', '*', 'D', 's', 'X', ',', 'o']

        marker_dict = {}
        line_style_dict = {}
        for i, algo in enumerate(exp.keys()):
            marker_dict[algo] = markers[i % len(markers)]
            line_style_dict[algo] = line_styles[i % len(line_styles)]
    else:
        algos_to_plot = []
        for algo in exp.keys():
            if algo.hidden:
                continue
            algos_to_plot.append(algo)

        # Assign colors without i % 10
        colors = {
            algo: colormap(i / max(1, len(algos_to_plot) - 1))  # Spread evenly in colormap
            for i, algo in enumerate(algos_to_plot)
        }

        # Assign markers
        markers = ['o', '^']
        marker_dict = {
            algo: markers[0] if i < len(markers) else markers[i % len(markers)]
            for i, algo in enumerate(algos_to_plot)
        }


    # Display the ratios
    if args.output_ratios:
        for k in ("metadata", "redundancy"):
            print_transmission_ratios(exp, k)

    if args.output_data:
        for k in ("total", "metadata", "redundancy"):
            print_transmitted(exp, k)


    transmitted = plot_metric(exp, colors, marker_dict, line_style_dict, lambda metric: metric.metadata, "Metadata", byte_formatter)
    name = f"{file}/transmitted.pdf"
    save_or_show(transmitted, name)


if __name__ == "__main__":
    main()
