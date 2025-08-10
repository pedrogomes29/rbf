# plots.py
# Plots the data gathered from experiements

import argparse
from collections import OrderedDict
import csv
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

Experiment = Dict[Algorithm, OrderedDict[float, List[Metrics]]]


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

    algorithm_files = [f for f in os.listdir(results_folder) if f.endswith('.csv')]    
    for alg_file in algorithm_files:
        algo_text = os.path.splitext(alg_file)[0]
        algo = read_algorithm(algo_text)
        if algo not in exp:
            exp[algo] = OrderedDict()
        
        file_path = os.path.join(results_folder, alg_file)
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                similarity = float(row[0])
                if similarity not in exp[algo]:
                    exp[algo][similarity] = []
                exp[algo][similarity].append(Metrics(
                    int(row[1]), # state
                    int(row[2]), # metadata
                    timedelta(microseconds=float(row[3])),  # t_enc
                    timedelta(microseconds=float(row[4])),  # t_dec
                ))

    return exp

def fmt_label(label: Algorithm) -> str:
    """Simple label format to be displayed in legend"""

    name = algorithm_abbreviations[label.name]

    if not label.params:
        return name

    params = f'[{", ".join(f"${k} = {v}$" for k, v in label.params.items())}]'
    return f"{name} {params}"

def plot_metric(exp: Experiment, colors: dict[Algorithm, ColorType], marker_dict: dict[Algorithm, str], line_style_dict: dict[Algorithm, str], metric_function: Callable[[Metrics],int], metric_name: str, y_formatter: ticker.EngFormatter) -> Figure:
    """Plot the result of applying metric_function to the measured metrics with multiple measurements"""
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.subplots_adjust(left=0.2, right=0.95, top=0.9, bottom=0.3)

    #ax.xaxis.set_major_formatter(percent_formatter)
    ax.yaxis.set_major_formatter(y_formatter)
    ax.grid(linestyle="--", linewidth=0.5, alpha=0.75)
    ax.set_xlabel("Set Difference Cardinality", fontsize=25)
    ax.set_ylabel(metric_name, fontsize=25, labelpad=8)
    ax.tick_params(axis="both", labelsize=20)
    
    ax.set_yscale('log')
    ax.set_xscale('log')


    legend_handles = []
    for algo, metrics_by_similarity in exp.items():
        # Get sorted similarity values and corresponding lists of measurements
        similarities = metrics_by_similarity.keys()
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

def main():
    """Script that extracts relevant data from logs and produces the plots for each experiment"""
    parser = argparse.ArgumentParser(prog="plots")
    parser.add_argument("files", nargs="*", default=("-"), type=argparse.FileType("r"))
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    
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

    transmitted = plot_metric(exp, colors, marker_dict, line_style_dict, lambda metric: metric.metadata + metric.state, "Data Transmitted", byte_formatter)
    name = f"{file}/transmitted.pdf"
    save_or_show(transmitted, name)


if __name__ == "__main__":
    main()
