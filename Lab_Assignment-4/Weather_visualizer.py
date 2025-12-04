############ Simple Weather Data Visualizer    ################
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_csv():
    filename = input("Enter CSV filename (default: weather.csv): ").strip()
    if filename == "":
        filename = "weather.csv"
    df = pd.read_csv(filename)
    print("\nFile loaded successfully.\n")
    return df

def clean_data(df):
    ########## detect date column ########
    date_col = None
    for c in df.columns:
        if "date" in c.lower():
            date_col = c
            break
    if date_col is None:
        date_col = df.columns[0]

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df = df.rename(columns={date_col: "date"})
    df = df.set_index("date").sort_index()

    ##### convert numeric columns ############
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    ######### fill missing values ##########
    if "rainfall" in df.columns:
        df["rainfall"] = df["rainfall"].fillna(0)
    df = df.fillna(method="ffill").fillna(df.mean())

    print("Data cleaned.\n")
    return df

def compute_stats(df):
    daily_mean = df.mean()
    monthly = df.resample("M").mean()
    yearly = df.resample("Y").mean()
    return daily_mean, monthly, yearly

def make_plots(df):
    plot_files = []

    #########  1 Temperature trend ############
    if "temperature" in df.columns:
        plt.figure(figsize=(10, 4))
        df["temperature"].plot()
        plt.title("Daily Temperature Trend")
        plt.xlabel("Date")
        plt.ylabel("Temperature")
        plt.tight_layout()
        plt.savefig("temp_trend.png")
        plt.close()
        plot_files.append("temp_trend.png")

    ##########  2 Monthly rainfall ##############
    if "rainfall" in df.columns:
        plt.figure(figsize=(10, 4))
        df["rainfall"].resample("M").sum().plot(kind="bar")
        plt.title("Monthly Rainfall")
        plt.xlabel("Month")
        plt.ylabel("Rainfall")
        plt.tight_layout()
        plt.savefig("monthly_rainfall.png")
        plt.close()
        plot_files.append("monthly_rainfall.png")

    ######## 3 Scatter humidity vs temp ###########
    if "temperature" in df.columns and "humidity" in df.columns:
        plt.figure(figsize=(6, 6))
        plt.scatter(df["temperature"], df["humidity"])
        plt.xlabel("Temperature")
        plt.ylabel("Humidity")
        plt.title("Humidity vs Temperature")
        plt.tight_layout()
        plt.savefig("humidity_vs_temp.png")
        plt.close()
        plot_files.append("humidity_vs_temp.png")

    ##########  4 Combined ############
    plt.figure(figsize=(12, 6))
    if "temperature" in df.columns:
        plt.subplot(2, 1, 1)
        df["temperature"].plot()
        plt.title("Temperature")

    if "rainfall" in df.columns:
        plt.subplot(2, 1, 2)
        df["rainfall"].resample("M").sum().plot(kind="bar")
        plt.title("Monthly Rainfall")

    plt.tight_layout()
    plt.savefig("combined.png")
    plt.close()
    plot_files.append("combined.png")

    print("Plots created.\n")
    return plot_files

def save_cleaned(df):
    df.to_csv("cleaned_weather.csv")
    print("Cleaned data saved to cleaned_weather.csv\n")

def save_report(daily_mean, monthly, yearly, plots):
    with open("weather_report.txt", "w") as f:
        f.write("Weather Summary Report\n")
        f.write("======================\n\n")

        f.write("Daily Mean Values:\n")
        for col, val in daily_mean.items():
            f.write(f"- {col}: {val:.2f}\n")

        f.write("\nPlots Saved:\n")
        for p in plots:
            f.write(f"- {p}\n")

    print("Report saved to weather_report.txt\n")

def main():
    print("=== Weather Data Visualizer ===\n")

    df_raw = load_csv()
    print(df_raw.head(), "\n")

    df = clean_data(df_raw)

    daily_mean, monthly, yearly = compute_stats(df)

    print("Daily Mean Values:")
    print(daily_mean)
    print()

    plots = make_plots(df)
    save_cleaned(df)
    save_report(daily_mean, monthly, yearly, plots)

    print("Processing complete.\n")

if __name__ == "__main__":
    main()
