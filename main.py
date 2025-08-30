import kookpy
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime, timedelta

def predict_and_plot_forecast(location_name):
    """
    Fetches the surf forecast, predicts the wave quality score for each time point,
    and plots the results in a color-coded graph.
    """
    print(f"Fetching 7-day forecast and predicting surf quality for {location_name}...")

    # Fetch the 7-day forecast data using the kookpy library
    forecast_df = kookpy.get_surf_forecast_by_name(location_name)

    if forecast_df.empty:
        print(f"Failed to fetch forecast data for {location_name}. Exiting.")
        return

    # Add a column for the predicted score
    forecast_df['wave_quality_score'] = forecast_df.apply(
        lambda row: kookpy.predict_surf_quality(row), axis=1
    )

    # Convert wave height from meters to feet for plotting
    forecast_df['swell_wave_height_ft'] = forecast_df['swell_wave_height'] * 3.281

    print("Prediction complete. Generating plot...")

    # Define the color map for the surf quality score
    cmap = LinearSegmentedColormap.from_list("mycmap", ["red", "yellow", "green"])

    # Create the figure and axes for two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    # --- First Subplot: Swell Wave Height with Quality Score ---
    sc = ax1.scatter(
        forecast_df['time'],
        forecast_df['swell_wave_height_ft'],
        c=forecast_df['wave_quality_score'],
        cmap=cmap,
        s=100,
        zorder=3
    )

    ax1.plot(
        forecast_df['time'],
        forecast_df['swell_wave_height_ft'],
        color='gray',
        linestyle='-',
        zorder=2,
    )

    ax1.set_title(f"Surf Forecast and Predicted Quality for {location_name}", fontsize=16)
    ax1.set_ylabel("Swell Wave Height (ft)", fontsize=12)
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

    cbar = fig.colorbar(sc, ax=ax1, orientation='vertical', pad=0.02)
    cbar.set_label("Predicted Wave Quality Score (1=Bad, 10=Good)", fontsize=12)

    # --- Second Subplot: Wind Speed ---
    ax2.plot(
        forecast_df['time'],
        forecast_df['wind_speed_10m'],
        color='skyblue',
        linestyle='--',
        label='Wind Speed (km/h)',
        zorder=1
    )
    ax2.set_title("Wind Speed Forecast", fontsize=14)
    ax2.set_xlabel("Date and Time", fontsize=12)
    ax2.set_ylabel("Wind Speed (km/h)", fontsize=12)
    ax2.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax2.legend(loc='upper left')

    # Formatting the x-axis for both subplots
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    fig.autofmt_xdate(rotation=45)

    plt.tight_layout()
    plt.show()

# Example Usage:
if __name__ == '__main__':
    # You will need to change this to a location you have trained a model for.
    location = "Laguna Beach"
    predict_and_plot_forecast(location)
