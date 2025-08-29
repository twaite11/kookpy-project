import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime

def geocode_location(location_name):
    """
    Finds the geographical coordinates (latitude and longitude) for a given location name.

    Args:
        location_name (str): The name of the location (e.g., "Laguna Beach").

    Returns:
        dict: A dictionary containing the latitude and longitude, or None if not found.
    """
    GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
    try:
        response = requests.get(GEOCODING_API_URL, params={'name': location_name, 'count': 1})
        response.raise_for_status()
        data = response.json()
        if data and 'results' in data and data['results']:
            location = data['results'][0]
            return {
                'latitude': location['latitude'],
                'longitude': location['longitude']
            }
    except requests.exceptions.RequestException as e:
        print(f"Error during geocoding API call: {e}")
    return None

def fetch_marine_data(latitude, longitude, start_date, end_date):
    """
    Fetches marine weather data from the Open-Meteo Marine API.

    Args:
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.
        start_date (str): The start date in 'YYYY-MM-DD' format.
        end_date (str): The end date in 'YYYY-MM-DD' format.

    Returns:
        pd.DataFrame: A DataFrame with the marine weather data.
    """
    MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
    marine_variables = [
        "swell_wave_height", "swell_wave_period", "swell_wave_direction",
        "wave_height", "wave_period", "wave_direction",
        "wind_wave_height", "wind_wave_period", "wind_wave_direction"
    ]
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(marine_variables),
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "auto"
    }
    try:
        response = requests.get(MARINE_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data['hourly'])
        df['time'] = pd.to_datetime(df['time'])
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error during marine API call: {e}")
    return pd.DataFrame()

def fetch_wind_data(latitude, longitude, start_date, end_date):
    """
    Fetches wind data from the appropriate Open-Meteo API (forecast or historical).

    Args:
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.
        start_date (str): The start date in 'YYYY-MM-DD' format.
        end_date (str): The end date in 'YYYY-MM-DD' format.

    Returns:
        pd.DataFrame: A DataFrame with the wind data.
    """
    # Determine the correct API endpoint based on the date range.
    today_str = datetime.now().strftime('%Y-%m-%d')
    if start_date < today_str:
        # Use the historical API for past dates
        API_URL = "https://archive-api.open-meteo.com/v1/archive"
    else:
        # Use the forecast API for today and future dates
        API_URL = "https://api.open-meteo.com/v1/forecast"

    wind_variables = ["wind_speed_10m", "wind_direction_10m"]
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(wind_variables),
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "auto"
    }
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data['hourly'])
        df['time'] = pd.to_datetime(df['time'])
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error during wind API call: {e}")
    return pd.DataFrame()

def plot_surf_data(df, location_name):
    """
    Creates a plot of swell and wind data.

    Args:
        df (pd.DataFrame): DataFrame containing the weather data.
        location_name (str): The name of the location for the plot title.
    """
    if df.empty:
        print("No data to plot.")
        return

    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot swell data on the primary y-axis
    ax1.plot(df['time'], df['swell_wave_height'], color='#FF5733', label='Swell Height (m)', marker='o')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Swell Height (m)', color='#FF5733')
    ax1.tick_params(axis='y', labelcolor='#FF5733')
    ax1.set_title(f'Swell and Wind Forecast for {location_name}', color='white')
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.5)

    # Create a secondary y-axis for wind data
    ax2 = ax1.twinx()
    ax2.plot(df['time'], df['wind_speed_10m'], color='#33FFC1', label='Wind Speed (km/h)', linestyle='--', marker='x')
    ax2.set_ylabel('Wind Speed (km/h)', color='#33FFC1')
    ax2.tick_params(axis='y', labelcolor='#33FFC1')

    # Add wind direction to the plot using annotations
    for i, row in df.iterrows():
        plt.text(
            row['time'],
            row['wind_speed_10m'],
            f"←",
            fontsize=10,
            color='#33FFC1',
            ha='center',
            va='bottom',
            rotation=-row['wind_direction_10m']
        )

    fig.tight_layout()
    plt.legend(loc='upper left')
    plt.show()

def get_surf_forecast_by_name(location_name):
    """
    Provides a surf forecast for a given beach name by combining geocoding and weather APIs.

    Args:
        location_name (str): The name of the beach or location.

    Returns:
        pd.DataFrame: A DataFrame with combined marine and wind data, or an empty DataFrame on failure.
    """
    print(f"Fetching surf data for {location_name}...")
    coords = geocode_location(location_name)
    if not coords:
        print(f"Could not find coordinates for {location_name}.")
        return pd.DataFrame()

    print(f"Found coordinates for {location_name}: Latitude {coords['latitude']}, Longitude {coords['longitude']}")

    today = datetime.now().strftime('%Y-%m-%d')

    marine_data = fetch_marine_data(coords['latitude'], coords['longitude'], today, today)
    wind_data = fetch_wind_data(coords['latitude'], coords['longitude'], today, today)

    if marine_data.empty and wind_data.empty:
        print("Failed to fetch data. Please check the beach name or network connection.")
        return pd.DataFrame()

    # Merge the two dataframes on the 'time' column
    combined_df = pd.merge(marine_data, wind_data, on='time', how='outer')
    return combined_df

if __name__ == '__main__':
    # Example usage:
    beach_name = "Laguna Beach"
    surf_forecast = get_surf_forecast_by_name(beach_name)

    if not surf_forecast.empty:
        plot_surf_data(surf_forecast, beach_name)
