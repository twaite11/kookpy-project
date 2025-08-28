import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Set up global variables for the API URL and relevant parameters.
# The Open-Meteo Marine Weather API is specifically designed for ocean data.
# These are open source non-commercial use API's!!!
MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"

# Use these variables for a comprehensive surf forecast.
# The marine API provides swell data.
# Two API's needed (the marine API doesn't have the supporting wind data..)
MARINE_VARIABLES = [
    "swell_wave_height",
    "swell_wave_period",
    "wave_direction",
]

# The standard weather API provides wind data.
WEATHER_VARIABLES = [
    "wind_speed_10m",
    "wind_direction_10m",
]


def get_surf_forecast_by_name(beach_name: str) -> pd.DataFrame:
    """
    Fetches surf forecast data for a given beach name.

    This function first uses the Open-Meteo Geocoding API to find the
    geographical coordinates of the beach. It then calls both the marine and
    standard weather APIs to get the combined forecast data.

    Args:
        beach_name (str): The name of the beach (e.g., "Mavericks").

    Returns:
        pd.DataFrame: A DataFrame containing the fetched hourly data.
                      Returns an empty DataFrame if the beach is not found or
                      the request fails.
    """
    try:
        # Step 1: Find coordinates using the Geocoding API
        geo_params = {"name": beach_name, "count": 1, "language": "en"}
        geo_response = requests.get(GEOCODING_API_URL, params=geo_params)
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if "results" not in geo_data or not geo_data["results"]:
            print(f"Error: Could not find coordinates for '{beach_name}'.")
            return pd.DataFrame()

        location_data = geo_data["results"][0]
        latitude = location_data["latitude"]
        longitude = location_data["longitude"]
        print(f"Found coordinates for {beach_name}: Latitude {latitude}, Longitude {longitude}")

        # Step 2: Fetch marine data using the found coordinates
        marine_data = fetch_data(MARINE_API_URL, latitude, longitude, MARINE_VARIABLES)

        # Step 3: Fetch wind data using the found coordinates
        wind_data = fetch_data(WEATHER_API_URL, latitude, longitude, WEATHER_VARIABLES)

        # Step 4: Merge the dataframes. This is crucial for plotting.
        if marine_data.empty or wind_data.empty:
            return pd.DataFrame()

        # Ensure the dataframes are aligned on their time index before merging
        combined_df = marine_data.join(wind_data)

        return combined_df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching geocoding data: {e}")
        return pd.DataFrame()

def fetch_data(api_url: str, latitude: float, longitude: float, variables: list) -> pd.DataFrame:
    """
    A generic function to fetch weather data from any Open-Meteo API.

    This function makes an HTTP GET request to the API URL, retrieves the JSON
    response, and converts it into a pandas DataFrame.

    Args:
        api_url (str): The URL of the Open-Meteo API.
        latitude (float): The geographical latitude of the location.
        longitude (float): The geographical longitude of the location.
        variables (list): A list of weather variables to request.

    Returns:
        pd.DataFrame: A DataFrame containing the fetched hourly data.
                      Returns an empty DataFrame if the request fails.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(variables),
        "timezone": "auto",
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if "hourly" not in data:
            print("Error: 'hourly' data not found in the API response.")
            return pd.DataFrame()

        hourly_data = data["hourly"]
        df = pd.DataFrame(hourly_data)

        # Convert the 'time' column to datetime objects for proper plotting.
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')

        return df
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {api_url}: {e}")
        return pd.DataFrame()


def plot_surf_data(df: pd.DataFrame, location_name: str):
    """
    Plots surf data including swell and wind metrics.

    This function creates a multi-panel plot to visualize the key surf
    forecasting metrics over time. Matplotlib is used for the visualization.

    Args:
        df (pd.DataFrame): DataFrame containing the swell and wind data.
        location_name (str): The name of the location for the plot title.
    """
    if df.empty:
        print("No data to plot.")
        return

    # Create a figure with two subplots for swell and wind data
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    # --- Swell Data Plot ---
    # Plot swell wave height
    ax1.plot(df.index, df['swell_wave_height'], marker='o', linestyle='-', color='b', label='Swell Wave Height')
    ax1.set_title(f"Surf Forecast for {location_name}")
    ax1.set_ylabel("Swell Wave Height (m) / Swell Wave Period (s)")
    ax1.grid(True)
    ax1.fill_between(df.index, df['swell_wave_height'], color='b', alpha=0.1)

    # Add swell wave period to the same plot
    ax1.plot(df.index, df['swell_wave_period'], marker='x', linestyle='--', color='g', label='Swell Wave Period')
    ax1.legend(loc='upper left')

    # Add swell wave direction as text annotations
    for i, txt in enumerate(df['wave_direction']):
        if i % 8 == 0:  # Annotate every 8th data point (roughly every 8 hours)
            ax1.annotate(
                f"{int(txt)}°",
                (mdates.date2num(df.index[i]), df['swell_wave_height'].iloc[i]),
                textcoords="offset points",
                xytext=(0, 10),
                ha='center',
                fontsize=8,
                color='r',
                fontweight='bold'
            )

    # --- Wind Data Plot ---
    # Plot wind speed
    ax2.plot(df.index, df['wind_speed_10m'], marker='o', linestyle='-', color='purple', label='Wind Speed')
    ax2.set_ylabel("Wind Speed (km/h)")
    ax2.set_xlabel("Date and Time")
    ax2.grid(True)
    ax2.fill_between(df.index, df['wind_speed_10m'], color='purple', alpha=0.1)

    # Add wind direction as text annotations
    for i, txt in enumerate(df['wind_direction_10m']):
        if i % 8 == 0:
            ax2.annotate(
                f"{int(txt)}°",
                (mdates.date2num(df.index[i]), df['wind_speed_10m'].iloc[i]),
                textcoords="offset points",
                xytext=(0, 10),
                ha='center',
                fontsize=8,
                color='red',
                fontweight='bold'
            )

    # Format the x-axis for better date readability
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # --- Example Usage for a beach name ---
    location_name = "Laguna Beach"

    print(f"Fetching surf data for {location_name}...")
    surf_data = get_surf_forecast_by_name(location_name)

    if not surf_data.empty:
        print("Data fetched successfully. Plotting now.")
        plot_surf_data(surf_data, location_name)
    else:
        print("Failed to fetch data. Please check the beach name or network connection.")
