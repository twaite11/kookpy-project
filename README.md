# kookpy
A Python library for fetching, visualizing, and analyzing comprehensive weather data from the Open-Meteo APIs for surf forecasting. This library is designed to be a foundation for building data-driven applications, including machine learning models for wave quality prediction.

## Features
* Location-Based Forecasts: 
Get surf and wind forecasts for any beach by simply providing its name. The library automatically fetches the geographical coordinates.

* Comprehensive Data: 
Retrieves both marine data (swell wave height, swell wave period, wave direction) and wind data (wind speed and direction).

* Data Visualization: 
Generates clear, multi-panel plots to visualize key swell and wind metrics over time using Matplotlib.

* Machine Learning Ready: 
Returns data in a Pandas DataFrame, making it simple to integrate with popular machine learning libraries like PyTorch and TensorFlow.

## Installation
This library requires Python 3.6+ and the following dependencies:

requests

pandas

matplotlib

You can install these using pip:

`pip install requests pandas matplotlib`

Usage
## 1. Getting a Surf Forecast by Beach Name
Use the get_surf_forecast_by_name function to get a combined forecast for a specific beach.

from kookpy import get_surf_forecast_by_name

### Fetch the data for a well-known surf spot
`surf_data = get_surf_forecast_by_name("Laguna Beach")`

`if not surf_data.empty:
    print(surf_data.head())`

## 2. Plotting the Data
Once you have the data in a Pandas DataFrame, you can use the plot_surf_data function to create a visualization.

from kookpy import plot_surf_data Assuming `surf_data` has already been fetched
plot_surf_data(surf_data, "Laguna Beach")

This will generate a two-panel plot showing swell wave height and period in the top panel, and wind speed and direction in the bottom panel.

## 3. As a Foundation for Machine Learning
The get_surf_forecast_by_name function returns a Pandas DataFrame, which is the standard input format for most data science libraries. You can use this data to train a machine learning model.

`import pandas as pd
from kookpy import get_surf_forecast_by_name`

## Fetch historical data (example)

`historical_data = get_surf_forecast_by_name(...)`

## Example of preparing data for a model
`features = historical_data[['swell_wave_height', 'swell_wave_period', 'wind_speed_10m', 'wind_direction_10m']]
target = historical_data['surf_quality_score'] # This would be your target variable`


Contributing
Contributions are welcome! If you have ideas for new features, improvements, or bug fixes, please feel free to open an issue or submit a pull request on the GitHub repository.

License
This project is licensed under the MIT License - see the LICENSE file for details.