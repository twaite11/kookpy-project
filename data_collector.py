import pandas as pd
import kookpy
from datetime import datetime, timedelta


def calculate_heuristic_score(row):
    """
    Calculates a heuristic wave quality score based on swell and wind data.
    - Higher swell_wave_height and swell_wave_period are better.
    - Lower wind_speed_10m is better.
    """
    # Define weights for each feature
    height_weight = 0.5
    period_weight = 0.4
    wind_weight = -0.1  # Negative weight for wind speed

    # Normalize values to a 0-10 scale for scoring
    normalized_height = min(row['swell_wave_height'], 3.0) / 3.0 * 10
    normalized_period = min(row['swell_wave_period'], 15.0) / 15.0 * 10
    normalized_wind = min(row['wind_speed_10m'], 30.0) / 30.0 * 10

    score = (height_weight * normalized_height) + \
            (period_weight * normalized_period) + \
            (wind_weight * normalized_wind)

    # Ensure the score is within a reasonable range
    score = max(1, min(10, score))
    return score

def collect_and_save_historical_data(location_name, start_date_str, end_date_str):
    """
    Collects historical surf data, calculates a quality score, and saves it to a CSV file.

    Args:
        location_name (str): The name of the beach to collect data for.
        start_date_str (str): The start date in 'YYYY-MM-DD' format.
        end_date_str (str): The end date in 'YYYY-MM-DD' format.
    """
    # Geocode the location to get coordinates
    coords = kookpy.geocode_location(location_name)
    if not coords:
        print(f"Error: Could not find coordinates for {location_name}.")
        return

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

    all_data = []

    current_date = start_date
    while current_date <= end_date:
        current_date_str = current_date.strftime('%Y-%m-%d')
        print(f"Fetching data for {current_date_str}...")

        try:
            # Fetch marine and wind data
            marine_data = kookpy.fetch_marine_data(coords['latitude'], coords['longitude'], current_date_str, current_date_str)
            wind_data = kookpy.fetch_wind_data(coords['latitude'], coords['longitude'], current_date_str, current_date_str)

            # Ensure both dataframes are not empty and merge
            if not marine_data.empty and not wind_data.empty:
                combined_df = pd.merge(marine_data, wind_data, on='time', how='inner')
                combined_df['wave_quality_score'] = combined_df.apply(calculate_heuristic_score, axis=1)
                all_data.append(combined_df)
            else:
                print(f"Could not fetch data for {current_date_str}. Skipping.")
        except Exception as e:
            print(f"Error fetching data for {current_date_str}: {e}")

        current_date += timedelta(days=1)

    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        # Drop rows with any missing values before saving
        full_df.dropna(inplace=True)

        if not full_df.empty:
            file_path = 'historical_surf_data.csv'
            full_df.to_csv(file_path, index=False)
            print(f"\nSuccessfully collected and saved {len(full_df)} data points to {file_path}")
        else:
            print("\nNo data was collected.")
    else:
        print("\nNo data was collected.")

if __name__ == '__main__':
    location = "Laguna Beach"
    start = "2023-01-01"
    end = "2024-01-01"
    collect_and_save_historical_data(location, start, end)
