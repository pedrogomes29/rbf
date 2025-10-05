# plots.py
# Plots the data gathered from experiements

import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42

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
import os


class Metrics(NamedTuple):
    state: int
    metadata: int
    theoretical_minimum: int
    t_enc: timedelta | None
    t_dec: timedelta | None


class Algorithm(NamedTuple):
    name: str
    params: dict[str, str]
    hidden: bool

    def __hash__(self) -> int:
        return hash((self.name, frozenset(self.params.items())))

Experiment = Dict[Algorithm, Dict[float, List[Metrics]]]
EXP_NAMES = ["similarity", "small_d"] 

percent_formatter = ticker.PercentFormatter()
byte_formatter = ticker.EngFormatter(unit="B")
bit_formatter = ticker.EngFormatter(unit="b")
second_formatter = ticker.EngFormatter(unit="s")
default_formatter = ticker.ScalarFormatter()
scientific_notation_formatter = ticker.EngFormatter(places=0, sep="\N{THIN SPACE}")

TOW_ESTIMATOR_METADATA = 336

algorithm_abbreviations = {
    "FullStateTransfer": "Full State Transfer",
    "Rateless": "RIBLT",
    "Bloom+Rateless": "SBF + RIBLT",
    "OptimalBloom+Rateless": "Optimal SBF + RIBLT",
    "RBloom+Rateless+ExpectedCost": "RBF + RIBLT",
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

    raw_exp = {}
    NO_REDUNDANT_STATE_ALGO_NAME = "PinSketch"
    NO_REDUNDANT_STATE_ALGO = None
    
    bloom_algorithms = {}

    algorithm_files = [f for f in os.listdir(results_folder) if f.endswith('.csv')]
    for alg_file in algorithm_files:
        algo_text = os.path.splitext(alg_file)[0]
        algo = read_algorithm(algo_text)
        if algo_text == NO_REDUNDANT_STATE_ALGO_NAME:
            NO_REDUNDANT_STATE_ALGO = algo
        if algo not in raw_exp:
            raw_exp[algo] = {}
        
        file_path = os.path.join(results_folder, alg_file)
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for trial_idx, row in enumerate(reader):
                nr_diffs = float(row[0])
                if nr_diffs not in raw_exp[algo]:
                    raw_exp[algo][nr_diffs] = []
                    
                state = int(row[1])
                metadata = int(row[2])
                if algo_text=="PBS" or algo_text=="PinSketch":
                    metadata += TOW_ESTIMATOR_METADATA
                
                t_enc = timedelta(microseconds=float(row[3]) / 1000) if row[3] != "0" else None
                t_dec = timedelta(microseconds=float(row[4]) / 1000) if row[4] != "0" else None

                # Store raw metrics temporarily
                raw_exp[algo][nr_diffs].append({
                    'state': state,
                    'metadata': metadata,
                    't_enc': t_enc,
                    't_dec': t_dec
                })

        # Store Bloom+Rateless algorithms separately for later analysis
        if algo.name == "Bloom+Rateless":
            bloom_algorithms[algo] = raw_exp[algo]
            
    if NO_REDUNDANT_STATE_ALGO is None:
        raise Exception(f"Expected {NO_REDUNDANT_STATE_ALGO_NAME} to be in experiences to extract theoretical minimum")
        
    # --- New Logic: Find Optimal Bloom+Rateless configuration ---
    optimal_bloom_data = {}
    
    # Get all the 'nr_diffs' values from the Bloom+Rateless algorithms
    all_diffs = set()
    for diff_data in bloom_algorithms.values():
        all_diffs.update(diff_data.keys())
    
    for nr_diffs in all_diffs:
        min_cost = float('inf')
        optimal_metrics = None
        
        for algo, diff_data in bloom_algorithms.items():
            if nr_diffs in diff_data:
                # Calculate the average communication cost for this FPR and diff
                avg_cost = np.mean([m['state'] + m['metadata'] for m in diff_data[nr_diffs]])
                
                if avg_cost < min_cost:
                    min_cost = avg_cost
                    optimal_metrics = diff_data[nr_diffs]

        if optimal_metrics:
            optimal_bloom_data[nr_diffs] = optimal_metrics
    
    if optimal_bloom_data:
        optimal_algo = Algorithm("OptimalBloom+Rateless", {}, False)
        raw_exp[optimal_algo] = optimal_bloom_data

    # --- End of New Logic ---

    exp = {}
    for algo, metrics_by_diffs in raw_exp.items():
        exp[algo] = {}
        for nr_diffs, metrics_list in metrics_by_diffs.items():
            exp[algo][nr_diffs] = []
            for trial_idx, metric_dict in enumerate(metrics_list):
                theoretical_min = raw_exp[NO_REDUNDANT_STATE_ALGO][nr_diffs][trial_idx]['state']
                # Create the final Metrics NamedTuple
                exp[algo][nr_diffs].append(Metrics(
                    state=metric_dict['state'],
                    metadata=metric_dict['metadata'],
                    t_enc=metric_dict['t_enc'],
                    t_dec=metric_dict['t_dec'],
                    theoretical_minimum=theoretical_min
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
    if metric.theoretical_minimum == 0:
        return None
    
    return (metric.state + metric.metadata) / metric.theoretical_minimum

def plot_metric(exp: Experiment, colors: dict[Algorithm, ColorType], marker_dict: dict[Algorithm, str], line_style_dict: dict[Algorithm, str], metric_function: Callable[[Metrics],int], filter_function: Callable[[Algorithm], bool], metric_name: str, x_formatter: ticker.EngFormatter, y_formatter: ticker.EngFormatter) -> Figure:
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
    #ax.set_ylim(top=275_000)
    ax.tick_params(axis="both", labelsize=15)

    legend_handles = []
    for algo, metrics_by_diffs in exp.items():
        if not filter_function(algo):
            continue
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
        ncol=2,
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

    exps = {}
    for exp_name in EXP_NAMES:
        exp = read_experiment(os.path.join(args.results_folder,exp_name))
        exps[exp_name] = exp

    all_algorithms = list({key for exp in exps.values() for key in exp.keys()})
    all_algorithms.sort(key=lambda alg: (alg.name, tuple(sorted(alg.params.items()))))

    colormap = colormaps.get_cmap("tab10")
    line_styles = ['solid','dotted','dashdot']
    markers = ['.', 'v', '*', 'D', 's', 'X', ',', 'o']

    marker_dict = {}
    line_style_dict = {}
    colors_dict = {}
    
    for i, algo in enumerate(all_algorithms):
        marker_dict[algo] = markers[i % len(markers)]
        line_style_dict[algo] = line_styles[i % len(line_styles)]
        colors_dict[algo] = colormap(i%10)

    for exp_name in EXP_NAMES:
        exp = exps[exp_name]
        
        def filter_sota_algos_function(algo:Algorithm) -> bool:
            return algo.name in ["PinSketch","Rateless", "PBS", "RBloom+Rateless+ExpectedCost", "FullStateTransfer"]
        
        
        
        #don't include full state transfer due to it's high overhead for low d
        communication_overhead_plot = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: compute_communication_overhead(metric), lambda algo: filter_sota_algos_function(algo) and algo.name!="FullStateTransfer", "Communication Overhead", scientific_notation_formatter, default_formatter)
        save_or_show(communication_overhead_plot, f"{exp_name}/sota_communication_overhead.pdf")
        
        transmitted_plot = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: metric.metadata + metric.state, filter_sota_algos_function, "Transmitted", scientific_notation_formatter, byte_formatter)
        save_or_show(transmitted_plot, f"{exp_name}/sota_transmitted_total.pdf")
        
        transmitted_metadata_plot = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: metric.metadata, lambda algo: filter_sota_algos_function(algo) and algo.name!="FullStateTransfer", "Metadata", scientific_notation_formatter, byte_formatter)
        save_or_show(transmitted_metadata_plot, f"{exp_name}/sota_transmitted_metadata.pdf")

        encoding_time_plot = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: metric.t_enc.total_seconds() if metric.t_enc is not None else None, filter_sota_algos_function, "Encoding Time", scientific_notation_formatter, second_formatter)
        save_or_show(encoding_time_plot, f"{exp_name}/sota_encoding_time.pdf")

        decoding_time_plot = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: metric.t_dec.total_seconds() if metric.t_dec is not None else None, filter_sota_algos_function, "Decoding Time", scientific_notation_formatter, second_formatter)
        save_or_show(decoding_time_plot, f"{exp_name}/sota_decoding_time.pdf")

        computation_time_plot = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: sum_times_seconds(metric), filter_sota_algos_function, "Computation Time", scientific_notation_formatter, second_formatter)
        save_or_show(computation_time_plot, f"{exp_name}/sota_computation_time.pdf")
        
        if exp_name=="small_d":
            encoding_time_plot_no_pinsketch = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: metric.t_enc.total_seconds() if metric.t_enc is not None else None, lambda algo: filter_sota_algos_function(algo) and algo.name!="PinSketch", "Encoding Time", scientific_notation_formatter, second_formatter)
            save_or_show(encoding_time_plot_no_pinsketch, f"{exp_name}/sota_encoding_time_no_pinsketch.pdf")

            decoding_time_plot_no_pinsketch = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: metric.t_dec.total_seconds() if metric.t_dec is not None else None, lambda algo: filter_sota_algos_function(algo) and algo.name!="PinSketch", "Decoding Time", scientific_notation_formatter, second_formatter)
            save_or_show(decoding_time_plot_no_pinsketch, f"{exp_name}/sota_decoding_time_no_pinsketch.pdf")

            computation_time_plot_no_pinsketch = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: sum_times_seconds(metric), lambda algo: filter_sota_algos_function(algo) and algo.name!="PinSketch", "Computation Time", scientific_notation_formatter, second_formatter)
            save_or_show(computation_time_plot_no_pinsketch, f"{exp_name}/sota_computation_time_no_pinsketch.pdf")

        
        if exp_name=="similarity":
            def filter_bf_vs_rbf_function(algo:Algorithm) -> bool:
                return algo.name in ["RBloom+Rateless+ExpectedCost", "OptimalBloom+Rateless"] or (algo.name=="Bloom+Rateless" and algo.params.get("\\epsilon") in ["1\\%","10\\%","25\\%"])

            
            communication_overhead_plot = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: compute_communication_overhead(metric), filter_bf_vs_rbf_function, "Communication Overhead", scientific_notation_formatter, default_formatter)
            save_or_show(communication_overhead_plot, f"{exp_name}/sbf_vs_rbf_communication_overhead.pdf")
            
            transmitted_plot = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: metric.metadata + metric.state, filter_bf_vs_rbf_function, "Transmitted", scientific_notation_formatter, byte_formatter)
            save_or_show(transmitted_plot, f"{exp_name}/sbf_vs_rbf_transmitted_total.pdf")
            
            transmitted_metadata_plot = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: metric.metadata, filter_bf_vs_rbf_function, "Metadata", scientific_notation_formatter, byte_formatter)
            save_or_show(transmitted_metadata_plot, f"{exp_name}/sbf_vs_rbf_transmitted_metadata.pdf")

            encoding_time_plot = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: metric.t_enc.total_seconds() if metric.t_enc is not None else None, filter_bf_vs_rbf_function, "Encoding Time", scientific_notation_formatter, second_formatter)
            save_or_show(encoding_time_plot, f"{exp_name}/sbf_vs_rbf_encoding_time.pdf")

            decoding_time_plot = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: metric.t_dec.total_seconds() if metric.t_dec is not None else None, filter_bf_vs_rbf_function, "Decoding Time", scientific_notation_formatter, second_formatter)
            save_or_show(decoding_time_plot, f"{exp_name}/sbf_vs_rbf_decoding_time.pdf")

            computation_time_plot = plot_metric(exp, colors_dict, marker_dict, line_style_dict, lambda metric: sum_times_seconds(metric), filter_bf_vs_rbf_function, "Computation Time", scientific_notation_formatter, second_formatter)
            save_or_show(computation_time_plot, f"{exp_name}/sbf_vs_rbf_computation_time.pdf")
        

if __name__ == "__main__":
    main()
