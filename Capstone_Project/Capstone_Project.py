########## Capstone_Project ###############
import os
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ------------------ Simple OOP models ------------------
class MeterReading:
    """A single meter reading: timestamp + kwh"""
    def __init__(self, timestamp: pd.Timestamp, kwh: float):
        self.timestamp = pd.to_datetime(timestamp)
        self.kwh = float(kwh)

class Building:
    """Represents a building and its meter readings (DataFrame)"""
    def __init__(self, name: str):
        self.name = name
        self.df = pd.DataFrame(columns=["timestamp", "kwh"])  # timestamp as index later

    def add_dataframe(self, df: pd.DataFrame):
        """Append cleaned dataframe with columns ['timestamp','kwh']"""
        self.df = pd.concat([self.df, df], ignore_index=True)

    def finalize(self):
        """Set timestamp index and sort"""
        if "timestamp" in self.df.columns:
            self.df["timestamp"] = pd.to_datetime(self.df["timestamp"], errors="coerce")
            self.df = self.df.dropna(subset=["timestamp"])
            self.df = self.df.sort_values("timestamp")
            self.df = self.df.set_index("timestamp")
            # ensure kwh numeric
            self.df["kwh"] = pd.to_numeric(self.df["kwh"], errors="coerce").fillna(0.0)

    def daily_totals(self) -> pd.Series:
        return self.df["kwh"].resample("D").sum()

    def weekly_totals(self) -> pd.Series:
        return self.df["kwh"].resample("W").sum()

    def total_consumption(self) -> float:
        return float(self.df["kwh"].sum())

    def mean_consumption(self) -> float:
        return float(self.df["kwh"].mean())

    def max_consumption(self) -> float:
        return float(self.df["kwh"].max())

# ------------------ Utility & ingestion ------------------
DATA_DIR = "data"

def find_csv_files(data_dir=DATA_DIR):
    """Return list of CSV file paths in data_dir"""
    if not os.path.isdir(data_dir):
        print(f"Data folder '{data_dir}' not found. Please create it and place CSV files inside.")
        return []
    files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.lower().endswith(".csv")]
    return files

def read_building_csv(path):
    try:
        # Use pandas with on_bad_lines if available; fallback if older pandas
        kwargs = {}
        try:
            # pandas >= 1.3 supports on_bad_lines
            kwargs["on_bad_lines"] = "skip"
        except Exception:
            pass
        df = pd.read_csv(path, **kwargs)
    except FileNotFoundError:
        print(f"File not found: {path}")
        return None
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None

    # find datetime-like column
    date_col = None
    for c in df.columns:
        if any(k in c.lower() for k in ("date", "time", "timestamp")):
            date_col = c
            break
    if date_col is None:
        # fallback to first column
        date_col = df.columns[0]

    # find kwh-like column
    kwh_col = None
    for c in df.columns:
        if any(k in c.lower() for k in ("kwh", "energy", "consumption", "usage")):
            kwh_col = c
            break
    if kwh_col is None:
        # try numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            kwh_col = numeric_cols[0]
        else:
            print(f"No kwh-like column found in {path}. Skipping file.")
            return None

    # Build cleaned DataFrame
    out = pd.DataFrame()
    out["timestamp"] = pd.to_datetime(df[date_col], errors="coerce")
    out["kwh"] = pd.to_numeric(df[kwh_col], errors="coerce")
    out = out.dropna(subset=["timestamp"])  # drop rows with bad timestamp
    # keep rows with non-negative kwh
    out["kwh"] = out["kwh"].fillna(0.0)
    return out

# ------------------ Aggregation & processing ------------------
def merge_buildings(files):
    """Read all CSVs, create Building objects, return dict of buildings"""
    buildings = {}
    for fpath in files:
        fname = os.path.basename(fpath)
        # infer building name from filename (without extension)
        bname = os.path.splitext(fname)[0]
        df = read_building_csv(fpath)
        if df is None or df.empty:
            print(f"Skipping {fname} (no usable data).")
            continue
        if bname not in buildings:
            buildings[bname] = Building(bname)
        buildings[bname].add_dataframe(df)
        print(f"Loaded {len(df)} rows from {fname} into building '{bname}'.")
    # finalize (set index, sort, convert kwh)
    for b in buildings.values():
        b.finalize()
    return buildings

def build_combined_dataframe(buildings: dict) -> pd.DataFrame:
    """Return merged DataFrame with columns: timestamp, building, kwh"""
    rows = []
    for bname, b in buildings.items():
        if b.df is None or b.df.empty:
            continue
        tmp = b.df.reset_index().copy()
        tmp["building"] = bname
        rows.append(tmp[["timestamp", "building", "kwh"]])
    if not rows:
        return pd.DataFrame(columns=["timestamp", "building", "kwh"])
    combined = pd.concat(rows, ignore_index=True)
    combined = combined.sort_values("timestamp")
    combined = combined.set_index("timestamp")
    return combined

def calculate_daily_weekly(combined_df):
    """Return daily_totals_df, weekly_totals_df (DataFrames indexed by date with building columns)"""
    if combined_df.empty:
        return pd.DataFrame(), pd.DataFrame()
    # daily
    daily = combined_df.reset_index().pivot_table(index="timestamp", columns="building", values="kwh", aggfunc="sum")
    daily = daily.resample("D").sum()
    # weekly
    weekly = daily.resample("W").sum()
    return daily, weekly

def building_summary(buildings: dict):
    """Return a DataFrame summarizing each building"""
    rows = []
    for bname, b in buildings.items():
        total = b.total_consumption()
        mean = b.mean_consumption() if not np.isnan(b.mean_consumption()) else 0.0
        peak = b.max_consumption()
        rows.append({"building": bname, "total_kwh": total, "mean_kwh": mean, "peak_kwh": peak})
    summary = pd.DataFrame(rows).set_index("building")
    summary = summary.sort_values("total_kwh", ascending=False)
    return summary

# ------------------ Visualization ------------------
def create_dashboard(daily_df, weekly_df, buildings_summary, out_file="dashboard.png"):
    """Create multi-chart dashboard and save as PNG"""
    plt.figure(figsize=(14, 10))
    # Subplot 1: daily trend lines for each building
    ax1 = plt.subplot(3, 1, 1)
    if not daily_df.empty:
        daily_df.plot(ax=ax1, legend=True, lw=1)
        ax1.set_title("Daily Consumption Trend (kWh) - per building")
        ax1.set_ylabel("kWh")

    # Subplot 2: bar chart average weekly usage (mean of weekly totals)
    ax2 = plt.subplot(3, 1, 2)
    if not weekly_df.empty:
        avg_weekly = weekly_df.mean().sort_values(ascending=False)
        avg_weekly.plot(kind="bar", ax=ax2)
        ax2.set_title("Average Weekly Usage (kWh)")
        ax2.set_ylabel("Avg kWh per week")

    # Subplot 3: scatter of peak hour consumption vs building (peak points)
    ax3 = plt.subplot(3, 1, 3)
    if not buildings_summary.empty:
        x = np.arange(len(buildings_summary))
        ax3.bar(x, buildings_summary["peak_kwh"])
        ax3.set_xticks(x)
        ax3.set_xticklabels(buildings_summary.index, rotation=45, ha="right")
        ax3.set_title("Peak Single-Reading (kWh) by Building")
        ax3.set_ylabel("Peak kWh")
    plt.tight_layout()
    plt.savefig(out_file)
    plt.close()
    print(f"Dashboard saved to {out_file}")

# ------------------ Persistence ------------------

def save_outputs(combined_df, buildings_summary):
    # cleaned combined CSV
    out_clean = "cleaned_energy_data.csv"
    if not combined_df.empty:
        combined_df.reset_index().to_csv(out_clean, index=False)
        print(f"Cleaned combined data saved to {out_clean}")
    else:
        print("No combined data to save.")

    # building summary CSV
    out_summary = "building_summary.csv"
    if not buildings_summary.empty:
        buildings_summary.reset_index().to_csv(out_summary, index=False)
        print(f"Building summary saved to {out_summary}")
    else:
        print("No building summary to save.")

    return out_clean, out_summary

def write_text_summary(buildings_summary, combined_df, out_file="summary.txt"):
    total_campus = combined_df["kwh"].sum() if not combined_df.empty else 0.0
    highest_building = buildings_summary.index[0] if not buildings_summary.empty else "N/A"
    highest_value = buildings_summary["total_kwh"].iloc[0] if not buildings_summary.empty else 0.0
    # peak time
    peak_time = combined_df["kwh"].idxmax() if not combined_df.empty else None
    with open(out_file, "w") as f:
        f.write("Campus Energy Use Summary\n")
        f.write("=========================\n\n")
        f.write(f"Total campus consumption (kWh): {total_campus:.2f}\n")
        f.write(f"Highest-consuming building: {highest_building} ({highest_value:.2f} kWh)\n")
        f.write(f"Peak single reading time: {peak_time}\n\n")
        f.write("Per-building totals (top 10):\n")
        if not buildings_summary.empty:
            f.write(buildings_summary.head(10).to_string())
        else:
            f.write("No building data available.\n")
    print(f"Summary text written to {out_file}")

# ------------------ Main flow ------------------
def main():
    print("=== Campus Energy-Use Dashboard ===")
    files = find_csv_files()
    if not files:
        print("No CSV files found in the data folder. Please add CSVs and rerun.")
        return

    print(f"Found {len(files)} CSV files. Reading and merging...")
    buildings = merge_buildings(files)
    if not buildings:
        print("No valid building data found after reading files.")
        return

    combined = build_combined_dataframe(buildings)
    daily_df, weekly_df = calculate_daily_weekly(combined)
    summary_df = building_summary(buildings)

    print("\nBuilding summary (top 5):")
    print(summary_df.head(5).to_string())

    # Visualization
    create_dashboard(daily_df, weekly_df, summary_df, out_file="dashboard.png")

    # Save outputs
    cleaned_csv, summary_csv = save_outputs(combined, summary_df)
    write_text_summary(summary_df, combined, out_file="summary.txt")

    print("\nAll done. Outputs: dashboard.png, cleaned_energy_data.csv, building_summary.csv, summary.txt")

if __name__ == "__main__":
    main()
