import os
import pickle
import math
from collections import defaultdict

ROOT_DIR = "."
OUTPUT_FILE = "output_pkl.txt"

results = []
channel_indices = {}

def load_pkl(filepath):
    with open(filepath, "rb") as f:
        return pickle.load(f)

def r3(x):
    try:
        return f"{float(x):.3f}"
    except:
        return ""

def mean(values):
    return sum(values) / len(values) if values else 0

def stdev(values):
    if len(values) < 2:
        return 0
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))

# --- LOAD DATA ---
for root, dirs, files in os.walk(ROOT_DIR):
    initial_file = None
    equalised_file = None

    for file in files:
        if file.startswith("threshold_scan_initial_") and file.endswith(".pkl"):
            initial_file = os.path.join(root, file)
        elif file.startswith("threshold_scan_equalised_") and file.endswith(".pkl"):
            equalised_file = os.path.join(root, file)

    if initial_file and equalised_file:
        initial_data = load_pkl(initial_file)
        equalised_data = load_pkl(equalised_file)

        for i in range(min(len(initial_data), len(equalised_data))):
            item_in = initial_data[i]
            item_eq = equalised_data[i]

            ch = item_in["channel"]

            channel_indices[ch] = channel_indices.get(ch, 0) + 1
            n_idx = channel_indices[ch]

            results.append({
                "channel": ch,
                "N": f"{n_idx:02d}",
                "peak_height_in": item_in["peak_height"],
                "sigma_in": item_in["sigma"],
                "FWHM_in": item_in["fwhm"],
                "peak_height_eq": item_eq["peak_height"],
                "sigma_eq": item_eq["sigma"],
                "FWHM_eq": item_eq["fwhm"],
            })

# --- SORT ---
results.sort(key=lambda x: (x["channel"], x["N"]))

# --- GROUP BY CHANNEL ---
grouped = defaultdict(list)
for entry in results:
    grouped[entry["channel"]].append(entry)

# --- COLUMN DEFINITIONS ---
columns = [
    ("CH", "[-]", "channel"),
    ("N", "[-]", "N"),
    ("peak_height_in", "[Hz]", "peak_height_in"),
    ("peak_height_eq", "[Hz]", "peak_height_eq"),
    ("σ_in", "[mV]", "sigma_in"),
    ("σ_eq", "[mV]", "sigma_eq"),
    ("FWHM_in", "[mV]", "FWHM_in"),
    ("FWHM_eq", "[mV]", "FWHM_eq"),
]

header_names = [c[0] for c in columns]
header_units = [c[1] for c in columns]

all_rows = [
    header_names,
    header_units
]

separator_placeholder = ["---"] * len(columns)

sorted_channels = sorted(grouped.keys())

# --- separator AFTER header (ONLY ONCE) ---
all_rows.append(separator_placeholder)

for idx, ch in enumerate(sorted_channels):
    group = grouped[ch]

    # --- separator BETWEEN groups (not before first group) ---
    if idx != 0:
        all_rows.append(separator_placeholder)

    # --- data rows ---
    for entry in group:
        row = []
        for _, _, key in columns:
            if key == "channel":
                row.append(str(entry["channel"]))
            elif key == "N":
                row.append(entry["N"])
            else:
                row.append(r3(entry.get(key)))
        all_rows.append(row)

    # --- stats ---
    stats = {}
    for _, _, key in columns:
        if key not in ["channel", "N"]:
            vals = [e[key] for e in group]
            stats[key] = {
                "mean": r3(mean(vals)),
                "std": r3(stdev(vals))
            }

    mean_row = []
    std_row = []

    for _, _, key in columns:
        if key == "channel":
            mean_row.append("mean")
            std_row.append("stddev")
        elif key in stats:
            mean_row.append(stats[key]["mean"])
            std_row.append(stats[key]["std"])
        else:
            mean_row.append("")
            std_row.append("")

    all_rows.append(mean_row)
    all_rows.append(std_row)

# --- ALIGNMENT ---
col_widths = []
for col_idx in range(len(columns)):
    col_widths.append(max(len(str(r[col_idx])) for r in all_rows))

def format_row(row):
    return "  ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row))

# --- FINAL SEPARATOR WIDTH ---
separator_row = ["-" * w for w in col_widths]

# replace placeholders
final_rows = [
    separator_row if r == separator_placeholder else r
    for r in all_rows
]

# --- WRITE FILE ---
with open(OUTPUT_FILE, "w") as f:
    for row in final_rows:
        f.write(format_row(row) + "\n")

print(f"Saved to {OUTPUT_FILE}")
