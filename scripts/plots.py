# plots.py
# Plots the data gathered from experiements

import argparse
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
    t_enc: timedelta | None
    t_dec: timedelta | None


class Algorithm(NamedTuple):
    name: str
    params: dict[str, str]
    hidden: bool

    def __hash__(self) -> int:
        return hash((self.name, frozenset(self.params.items())))

Experiment = Dict[Algorithm, Dict[float, List[Metrics]]]


percent_formatter = ticker.PercentFormatter()
byte_formatter = ticker.EngFormatter(unit="B")
bit_formatter = ticker.EngFormatter(unit="b")
second_formatter = ticker.EngFormatter(unit="s")
default_formatter = ticker.ScalarFormatter()
scientific_notation_formatter = ticker.EngFormatter(places=0, sep="\N{THIN SPACE}")

TOW_ESTIMATOR_METADATA = 336

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
    "RBloom+Rateless+NoParams": "RbRsCo",
    "PinSketch": "PinSketch",
    "PBS": "PBS"
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
        #if algo_text in ["PinSketch"]:
        #    continue
        #if algo_text not in ["PinSketch", "Rateless","RBloom+Rateless+NoParams[m=1.4426950408889634,]"]:
        #    continue
        algo = read_algorithm(algo_text)
        if algo not in exp:
            exp[algo] = {}
        
        file_path = os.path.join(results_folder, alg_file)
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                nr_diffs = float(row[0])
                if nr_diffs not in exp[algo]:
                    exp[algo][nr_diffs] = []
                    
                state = int(row[1])
                metadata = int(row[2])
                if algo_text=="PBS" or algo_text=="PinSketch":
                    metadata += TOW_ESTIMATOR_METADATA
                
                t_enc = timedelta(microseconds=float(row[3]) / 1000) if row[3] != "0" else None  # t_enc
                t_dec = timedelta(microseconds=float(row[4]) / 1000) if row[4] != "0" else None  # t_dec

            
                exp[algo][nr_diffs].append(Metrics(
                    state,
                    metadata,
                    t_enc,
                    t_dec
                ))                
                



    return exp

def fmt_label(label: Algorithm) -> str:
    """Simple label format to be displayed in legend"""

    name = algorithm_abbreviations[label.name]

    if not label.params:
        return name

    params = f'[{", ".join(f"${k} = {v}$" for k, v in label.params.items())}]'
    return f"{name} {params}"

def sum_times_seconds(metrics: Metrics) -> float | None:
    t_enc = metrics.t_enc
    t_dec = metrics.t_dec
    
    if t_enc is None or t_dec is None:
        return None
    
    return t_enc.total_seconds() + t_dec.total_seconds()

def compute_communication_overhead(metric: Metrics) -> float | None:
    if metric.state == 0:
        return None
    
    return (metric.state + metric.metadata) / metric.state

def plot_metric(exp: Experiment, colors: dict[Algorithm, ColorType], marker_dict: dict[Algorithm, str], line_style_dict: dict[Algorithm, str], metric_function: Callable[[Metrics],int], metric_name: str, x_formatter: ticker.EngFormatter, y_formatter: ticker.EngFormatter) -> Figure:
    """Plot the result of applying metric_function to the measured metrics with multiple measurements"""
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.subplots_adjust(left=0.2, right=0.95, top=0.9, bottom=0.3)

    ax.xaxis.set_major_formatter(x_formatter)
    ax.yaxis.set_major_formatter(y_formatter)
    ax.grid(linestyle="--", linewidth=0.5, alpha=0.75)
    ax.set_xlabel("Set Difference Cardinality", fontsize=20, labelpad=8)
    ax.set_ylabel(metric_name, fontsize=20, labelpad=8)
    #ax.set_xscale('log')
    #ax.set_yscale('log')
    ax.tick_params(axis="both", labelsize=15)

    legend_handles = []
    for algo, metrics_by_diffs in exp.items():
        # Get sorted similarity values and corresponding lists of measurements
        diffs = sorted(metrics_by_diffs.keys())
        
        
        # Filter out similarities with no valid data
        filtered_diffs = []
        filtered_measurements_list = []
        
        for d in diffs:
            valid_measurements = [metric_function(m) for m in metrics_by_diffs[d] if metric_function(m) is not None]
            if valid_measurements:
                filtered_diffs.append(d)
                filtered_measurements_list.append(valid_measurements)

        if not filtered_diffs:
            continue

        # Calculate mean and standard deviation for the filtered data
        means = [np.mean(m) for m in filtered_measurements_list]
        stds = [np.std(m) for m in filtered_measurements_list]
        
        color = colors[algo]
        label = fmt_label(algo)
        marker = marker_dict[algo]
        line_style = line_style_dict[algo]

        line_handle, = ax.plot(filtered_diffs, means, marker=marker, linestyle=line_style, color=color, lw=2, label=label, markersize=8)
        legend_handles.append(line_handle)

        # Plot the shaded area for standard deviation
        ax.fill_between(
            filtered_diffs,
            np.array(means) - np.array(stds),
            np.array(means) + np.array(stds),
            color=color,
            alpha=0.2
        )

    # Adjust the legend to be outside the plot area
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        ncol=3,
        frameon=False,
        fontsize=15,
        title_fontsize=30
    )

    return fig

def main():
    """Script that extracts relevant data from logs and produces the plots for each experiment"""
    parser = argparse.ArgumentParser(prog="plots")
    parser.add_argument("results_folder",)
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


    exp = read_experiment(args.results_folder)
        
        
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

    communication_overhead_plot = plot_metric(exp, colors, marker_dict, line_style_dict, lambda metric: compute_communication_overhead(metric), "Communication Overhead", scientific_notation_formatter, default_formatter)
    save_or_show(communication_overhead_plot, "communication_overhead.pdf")
    
    transmitted_plot = plot_metric(exp, colors, marker_dict, line_style_dict, lambda metric: metric.metadata + metric.state, "Transmitted", scientific_notation_formatter, byte_formatter)
    save_or_show(transmitted_plot, "transmitted_total.pdf")
    
    transmitted_metadata_plot = plot_metric(exp, colors, marker_dict, line_style_dict, lambda metric: metric.metadata, "Metadata", scientific_notation_formatter, byte_formatter)
    save_or_show(transmitted_metadata_plot, "transmitted_metadata.pdf")

    encoding_time_plot = plot_metric(exp, colors, marker_dict, line_style_dict, lambda metric: metric.t_enc.total_seconds() if metric.t_enc is not None else None, "Encoding Time", scientific_notation_formatter, second_formatter)
    save_or_show(encoding_time_plot, "encoding_time.pdf")

    decoding_time_plot = plot_metric(exp, colors, marker_dict, line_style_dict, lambda metric: metric.t_dec.total_seconds() if metric.t_dec is not None else None, "Decoding Time", scientific_notation_formatter, second_formatter)
    save_or_show(decoding_time_plot, "decoding_time.pdf")

    computation_time_plot = plot_metric(exp, colors, marker_dict, line_style_dict, lambda metric: sum_times_seconds(metric), "Computation Time", scientific_notation_formatter, second_formatter)
    save_or_show(computation_time_plot, "computation_time_pinsketch.pdf")

if __name__ == "__main__":
    main()
