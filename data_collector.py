import kookpy
import pandas as pd
from datetime import datetime, timedelta
import os
import time

def calculate_heuristic_score(df):
    """
    Calculates a heuristic wave quality score based on swell height, period, and wind speed.

    Current: Wave quality score is calculated by weighted scores for wave height (bigger = better),
    wave period (greater = better), and wind speed (less = better).

    Args:
        df (pd.DataFrame): DataFrame with surf and wind data.

    Returns:
        pd.DataFrame: DataFrame with the added 'wave_quality_score' column.
    """
    # Define a simple formula for wave quality
    # A higher score means better waves.
    # Swell Height and Period are positive factors, Wind Speed is a negative factor.
    df['wave_quality_score'] = (
            (0.5 * df['swell_wave_height']) +
            (0.4 * df['swell_wave_period']) -
            (0.1 * df['wind_speed_10m'])
    )
    # Ensure the score is not negative
    df['wave_quality_score'] = df['wave_quality_score'].apply(lambda x: max(0, x))
    return df

def collect_and_save_historical_data(location_name, start_date_str, end_date_str):
    """
    Collects historical marine and wind data and saves it to a CSV file.

    Args:
        location_name (str): The name of the beach.
        start_date_str (str): Start date in YYYY-MM-DD format.
        end_date_str (str): End date in YYYY-MM-DD format.
    """
    coords = kookpy.geocode_location(location_name)
    if not coords:
        print(f"Could not find coordinates for {location_name}. Exiting.")
        return

    print(f"Starting data collection for {location_name} from {start_date_str} to {end_date_str}...")

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    all_data = []
    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"Fetching data for {date_str}...")

        # Fetch marine and wind data for the current day
        marine_data = kookpy.fetch_marine_data(coords['latitude'], coords['longitude'], date_str, date_str)
        wind_data = kookpy.fetch_wind_data(coords['latitude'], coords['longitude'], date_str, date_str)

        # Merge the dataframes. An 'inner' join ensures we only keep rows
        # where both marine and wind data are available for that specific hour.
        if not marine_data.empty and not wind_data.empty:
            merged_data = pd.merge(marine_data, wind_data, on='time', how='inner')

            if not merged_data.empty:
                # Calculate the wave quality score
                scored_data = calculate_heuristic_score(merged_data)
                all_data.append(scored_data)
                print(f"Successfully collected data for {date_str}.")
            else:
                print(f"No matching data found for {date_str}. Skipping.")
        else:
            print(f"Could not fetch data for {date_str}. Skipping.")

        # Move to the next day
        current_date += timedelta(days=1)
        time.sleep(1) # Be a good web citizen

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        # Drop any remaining rows with missing values that might have slipped through
        combined_df.dropna(inplace=True)

        output_file = "historical_surf_data.csv"
        combined_df.to_csv(output_file, index=False)
        print(f"\nData collection complete. Saved to '{output_file}'.")
    else:
        print("\nNo data was collected.")


if __name__ == '__main__':
    # You can change the location name and date range here
    location = "Laguna Beach"
    start_date = "2024-01-01"
    end_date = "2024-01-05"
    collect_and_save_historical_data(location, start_date, end_date)
