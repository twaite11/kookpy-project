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

streamlit

plotly

You can install these using pip:

`pip install requests pandas matplotlib streamlit plotly`

Usage
## 1. Collect Historical Data 
You need historical data to train the prediction model. Use the data_collector.py script to fetch data from the past. You can customize the location and date range within the script.

### Run the data collector and select your beach 
`python data_collector.py`

This will write over/create `historical_surf_data.csv` file in your project directory


## 2. Train the Prediction Model 
The `model_trainer.py` script will train a TensorFlow model on your collected data. It uses a heuristic to create a `wave_quality_score` based on swell height, period, and wind speed.

`python model_trainer.py`

After running this script, three files will be created in your directory: `wave_prediction_model.keras`, `scaler_X.pkl`, and `scaler_y.pkl`. These files are essential for making predictions.
## 3. Make Predictions and Visualize
The `main.py` script is your primary application. It fetches the latest forecast, uses your trained model to predict a surf quality score for each time point, and visualizes the results.

`python main.py`

### The script will generate two graphs:
a. **Swell Wave Height:** A line graph showing the swell height in feet, with color-coded points representing the predicted wave quality score (red=bad, green=good).

b. **Wind Speed:** A separate line graph showing the forecasted wind speed in km/h.
## Directory Structure

For everything to work correctly, your project should have the following structure:

`kookpy-project/                                                         
├── kookpy/
│   ├── __init__.py
├── data_collector.py
├── model_trainer.py
├── main.py
└── README.md`

Contact
For questions or contributions, please contact tyco711@gmail.com or open an issue on the GitHub repository.

Contributions are welcome! If you have ideas for new features, improvements, or bug fixes, please feel free to open an issue or submit a pull request on the GitHub repository.

License
This project is licensed under the MIT License - see the LICENSE file for details.
