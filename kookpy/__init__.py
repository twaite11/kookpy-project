import requests
import pandas as pd
import tensorflow as tf
import joblib
from datetime import datetime, timedelta
import time
import os

# Base URLs for the Open-Meteo APIs
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_WEATHER_API_URL = "https://archive-api.open-meteo.com/v1/archive"


def geocode_location(location_name):
    """
    Converts a location name to geographical coordinates (latitude and longitude).

    Args:
        location_name (str): The name of the beach or city.

    Returns:
        dict: A dictionary containing 'latitude' and 'longitude', or None if not found.
    """
    try:
        response = requests.get(f"{GEOCODING_API_URL}?name={location_name}")
        response.raise_for_status()
        data = response.json()
        if 'results' in data and data['results']:
            # Return the coordinates of the first result
            return {
                'latitude': data['results'][0]['latitude'],
                'longitude': data['results'][0]['longitude']
            }
    except requests.exceptions.RequestException as e:
        print(f"Error during geocoding API call: {e}")
        return None
    return None


def fetch_marine_data(latitude, longitude, start_date, end_date):
    """
    Fetches marine weather data (swell and waves) from Open-Meteo.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.

    Returns:
        pd.DataFrame: A DataFrame with the marine data.
    """
    url = MARINE_API_URL
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "swell_wave_height,swell_wave_period,wave_direction",
        "start_date": start_date,
        "end_date": end_date
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if 'hourly' in data:
            df = pd.DataFrame(data['hourly'])
            df['time'] = pd.to_datetime(df['time'])
            return df
    except requests.exceptions.RequestException as e:
        print(f"Error during marine API call: {e}")
        return pd.DataFrame()
    return pd.DataFrame()


def fetch_wind_data(latitude, longitude, start_date, end_date):
    """
    Fetches wind data from Open-Meteo. Automatically switches to the historical
    API for past dates.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.

    Returns:
        pd.DataFrame: A DataFrame with the wind data.
    """
    is_historical = datetime.strptime(start_date, '%Y-%m-%d').date() < datetime.now().date()

    url = HISTORICAL_WEATHER_API_URL if is_historical else WEATHER_API_URL

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "wind_speed_10m,wind_direction_10m",
        "start_date": start_date,
        "end_date": end_date
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if 'hourly' in data:
            df = pd.DataFrame(data['hourly'])
            df['time'] = pd.to_datetime(df['time'])
            return df
    except requests.exceptions.RequestException as e:
        print(f"Error during wind API call: {e}")
        return pd.DataFrame()
    return pd.DataFrame()


def plot_surf_data(df, location_name):
    """
    Plots surf-related data using Matplotlib.

    Args:
        df (pd.DataFrame): DataFrame containing surf data.
        location_name (str): The name of the location for the plot title.
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        # Convert wave height from meters to feet
        df['swell_wave_height_ft'] = df['swell_wave_height'] * 3.281

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        # Plot Swell Wave Height on the first subplot
        ax1.plot(df['time'], df['swell_wave_height_ft'], label='Swell Wave Height (ft)', color='blue')
        ax1.set_title(f'Swell and Wind Forecast for {location_name}')
        ax1.set_ylabel('Wave Height (ft)')
        ax1.legend()
        ax1.grid(True)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

        # Plot Wind Speed on the second subplot
        ax2.plot(df['time'], df['wind_speed_10m'], label='Wind Speed (km/h)', color='green')
        ax2.set_ylabel('Wind Speed (km/h)')
        ax2.set_xlabel('Date and Time')
        ax2.legend()
        ax2.grid(True)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

        fig.tight_layout()
        plt.xticks(rotation=45)
        plt.show()

    except ImportError:
        print("Matplotlib is not installed. Please install it with 'pip install matplotlib'.")


def get_surf_forecast_by_name(location_name):
    """
    Fetches the 7-day surf forecast (marine and wind data) for a given location name.

    Args:
        location_name (str): The name of the beach or city.

    Returns:
        pd.DataFrame: A DataFrame with combined marine and wind forecast data.
    """
    coords = geocode_location(location_name)
    if not coords:
        return pd.DataFrame()

    today = datetime.now().date()
    end_date = today + timedelta(days=6)

    marine_data = fetch_marine_data(coords['latitude'], coords['longitude'], today.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    wind_data = fetch_wind_data(coords['latitude'], coords['longitude'], today.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

    if not marine_data.empty and not wind_data.empty:
        # Before merging, check for non-empty dataframes.
        if not marine_data.empty and not wind_data.empty:
            combined_df = pd.merge(marine_data, wind_data, on='time', how='outer')
            return combined_df
        else:
            return pd.DataFrame()
    else:
        return pd.DataFrame()

def predict_surf_quality(data_point):
    """
    Predicts the surf quality score for a single data point using a trained
    TensorFlow model.

    Args:
        data_point (pd.Series or dict): A single data point containing the
                                        required features for prediction.

    Returns:
        float: The predicted wave quality score. Returns None if prediction fails.
    """
    # 1. Check if model and scalers exist
    if not os.path.exists('wave_prediction_model.keras') or \
       not os.path.exists('scaler_X.pkl') or \
       not os.path.exists('scaler_y.pkl'):
        print("Error: The trained model files were not found.")
        print("Please run 'model_trainer.py' first to generate them.")
        return None

    # 2. Load the trained model and scalers
    try:
        model = tf.keras.models.load_model('wave_prediction_model.keras')
        scaler_X = joblib.load('scaler_X.pkl')
        scaler_y = joblib.load('scaler_y.pkl')
    except Exception as e:
        print(f"Error loading model files: {e}")
        return None

    # 3. Prepare the data for prediction
    # Ensure the input data has the correct features and shape
    features = ['swell_wave_height', 'swell_wave_period', 'wind_speed_10m']

    try:
        # Convert the single data point to a DataFrame with a single row
        new_data_df = pd.DataFrame([data_point[features].values], columns=features)

        # Scale the new data using the loaded scaler
        new_data_scaled = scaler_X.transform(new_data_df)

        # Make the prediction
        predicted_scaled = model.predict(new_data_scaled)

        # Inverse transform to get the original score
        predicted_score = scaler_y.inverse_transform(predicted_scaled)

        return predicted_score[0][0]
    except KeyError as e:
        print(f"Error: Missing feature in data point: {e}. Required features are {features}")
        return None
    except Exception as e:
        print(f"Error during prediction: {e}")
        return None

if __name__ == '__main__':
    # This block can be used to test the library's functionality
    location_name = "Laguna Beach"

    # Demonstrate data fetching
    forecast_data = get_surf_forecast_by_name(location_name)
    if not forecast_data.empty:
        print(f"Successfully fetched a 7-day forecast for {location_name}.")
        print("First 5 rows of data:")
        print(forecast_data.head())
        # Plotting the data
        # plot_surf_data(forecast_data, location_name)
    else:
        print(f"Failed to fetch forecast data for {location_name}.")

    # Demonstrate prediction
    # This will only work if you have run model_trainer.py first
    predicted_score = predict_surf_quality(location_name)
    if predicted_score is not None:
        print(f"\nPredicted Surf Quality Score for {location_name}: {predicted_score:.2f}")
