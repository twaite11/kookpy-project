import requests
import pandas as pd
import tensorflow as tf
import joblib
from datetime import datetime, timedelta
import time
import os
import numpy as np
import streamlit as st

# Base URLs for the Open-Meteo APIs
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_WEATHER_API_URL = "https://archive-api.open-meteo.com/v1/archive"


# Use Streamlit's resource caching to load the model only once
@st.cache_resource
def load_model(path='wave_prediction_model.keras'):
    """Loads the pre-trained TensorFlow model from disk."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found at {path}. Please run model_trainer.py first.")
    return tf.keras.models.load_model(path)

# Use Streamlit's resource caching to load the scalers only once
@st.cache_resource
def load_scalers(scaler_X_path='scaler_X.pkl', scaler_y_path='scaler_y.pkl'):
    """Loads the data scalers from disk."""
    if not os.path.exists(scaler_X_path) or not os.path.exists(scaler_y_path):
        raise FileNotFoundError("Scaler files not found. Please run model_trainer.py first.")
    scaler_X = joblib.load(scaler_X_path)
    scaler_y = joblib.load(scaler_y_path)
    return scaler_X, scaler_y


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
        "hourly": "swell_wave_height,swell_wave_period,wave_direction,sea_level_height_msl",
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

def fetch_tide_data(latitude, longitude, start_date, end_date):
    """
    Fetches tide data (sea level height) from Open-Meteo and finds the next high and low tides.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.

    Returns:
        dict: A dictionary with 'next_high_tide' and 'next_low_tide' information, or None if no data is found.
    """
    url = MARINE_API_URL
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "sea_level_height_msl",
        "start_date": start_date,
        "end_date": end_date
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if 'hourly' in data and data['hourly']['sea_level_height_msl']:
            df = pd.DataFrame(data['hourly'])
            df['time'] = pd.to_datetime(df['time'])
            df['sea_level_height_msl'] = df['sea_level_height_msl'].replace(-999, np.nan) # Handle missing values

            # Use a rolling window to find local minima and maxima
            is_max = df['sea_level_height_msl'] == df['sea_level_height_msl'].rolling(window=3, center=True).max()
            is_min = df['sea_level_height_msl'] == df['sea_level_height_msl'].rolling(window=3, center=True).min()

            high_tides = df[is_max].dropna()
            low_tides = df[is_min].dropna()

            now = datetime.now()
            next_high_tide = high_tides[high_tides['time'] > now].iloc[0] if not high_tides[high_tides['time'] > now].empty else None
            next_low_tide = low_tides[low_tides['time'] > now].iloc[0] if not low_tides[low_tides['time'] > now].empty else None

            result = {}
            if next_high_tide is not None:
                result['next_high_tide'] = {
                    'time': next_high_tide['time'].strftime('%H:%M %p'),
                    'height_m': next_high_tide['sea_level_height_msl']
                }
            if next_low_tide is not None:
                result['next_low_tide'] = {
                    'time': next_low_tide['time'].strftime('%H:%M %p'),
                    'height_m': next_low_tide['sea_level_height_msl']
                }

            return result if result else None

    except requests.exceptions.RequestException as e:
        print(f"Error during tide API call: {e}")
    except Exception as e:
        print(f"Error processing tide data: {e}")
    return None

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
        combined_df = pd.merge(marine_data, wind_data, on='time', how='inner')
        return combined_df
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
    model = load_model()
    scaler_X, scaler_y = load_scalers()

    features = ['swell_wave_height', 'swell_wave_period', 'wind_speed_10m', 'sea_level_height_msl']

    try:
        new_data_df = pd.DataFrame([data_point[features].values], columns=features)

        new_data_scaled = scaler_X.transform(new_data_df)

        predicted_scaled = model.predict(new_data_scaled)

        predicted_score = scaler_y.inverse_transform(predicted_scaled)

        return float(predicted_score[0][0])
    except KeyError as e:
        print(f"Error: Missing feature in data point: {e}. Required features are {features}")
        return None
    except Exception as e:
        print(f"Error during prediction: {e}")
        return None
