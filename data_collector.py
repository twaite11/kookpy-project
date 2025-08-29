import kookpy
import pandas as pd
import time
from datetime import datetime, timedelta

def collect_and_save_historical_data(location_name, start_date, end_date, output_file):
    """
    Collects historical marine and wind data and saves it to a CSV file.

    This function uses the kookpy library to fetch data for a given date range
    and location, then stores it in a pandas DataFrame for future use in
    machine learning model training.

    Args:
        location_name (str): The name of the beach or location to fetch data for.
        start_date (str): The start date in 'YYYY-MM-DD' format.
        end_date (str): The end date in 'YYYY-MM-DD' format.
        output_file (str): The path to the CSV file where the data will be saved.
    """
    all_data = []
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')

    print(f"Starting data collection for {location_name} from {start_date} to {end_date}...")

    while current_date <= end_datetime:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"Fetching data for {date_str}...")

        try:
            # Fetch both marine and wind data from the APIs
            marine_data = kookpy.fetch_marine_data(
                latitude=kookpy.geocode_location(location_name)['latitude'],
                longitude=kookpy.geocode_location(location_name)['longitude'],
                start_date=date_str,
                end_date=date_str
            )
            wind_data = kookpy.fetch_wind_data(
                latitude=kookpy.geocode_location(location_name)['latitude'],
                longitude=kookpy.geocode_location(location_name)['longitude'],
                start_date=date_str,
                end_date=date_str
            )

            # Combine the DataFrames
            if not marine_data.empty and not wind_data.empty:
                combined_data = pd.merge(marine_data, wind_data, on='time', how='outer')
                all_data.append(combined_data)
                print(f"Successfully fetched and combined data for {date_str}.")
            else:
                print(f"Could not fetch data for {date_str}. Skipping.")

        except Exception as e:
            print(f"Error fetching data for {date_str}: {e}")

        current_date += timedelta(days=1)
        time.sleep(1) # Be a good citizen and don't spam the API

    # Concatenate all collected dataframes and save to CSV
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv(output_file, index=False)
        print(f"\nData collection complete. Saved data to {output_file}")
    else:
        print("\nNo data was collected.")

if __name__ == '__main__':
    # Define the location, date range, and output file
    location = "Laguna Beach"
    # Note: Use a larger date range for real training data
    start_date = "2024-01-01"
    end_date = "2024-01-05"
    output_file = "historical_surf_data.csv"

    # Start the data collection process
    collect_and_save_historical_data(location, start_date, end_date, output_file)
