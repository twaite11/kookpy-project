import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import kookpy
from datetime import datetime

# Set up the page configuration
st.set_page_config(layout="wide", page_title="Kookpy AI Surf Forecast")

# Main application title and description
st.title("Kookpy AI Surf Forecast")
st.markdown("### Powered by the Open-Meteo API and TensorFlow")
st.write("Enter a beach name to get the 7-day surf and wind forecast, along with a predicted wave quality score. The model predicts scores on a scale from 1 (bad) to 10 (good).")

# --- User Input Section ---
st.markdown("---")
# Tabs for different input methods
tabs = st.tabs(["Search by Name", "Select from List"])

with tabs[0]:
    beach_name_input = st.text_input("Enter a beach name:", "Laguna Beach", help="e.g., Laguna Beach, Huntington Beach, Waikiki")
    if st.button("Get Forecast & Prediction", type="primary"):
        if not beach_name_input:
            st.error("Please enter a valid beach name.")
        else:
            st.session_state.run_forecast = True
            st.session_state.beach_name = beach_name_input

with tabs[1]:
    california_beaches = [
        "Laguna Beach", "Huntington Beach", "Malibu", "Santa Cruz", "La Jolla",
        "Trestles", "Steamer Lane", "Rincon", "Newport Beach", "Pacifica State Beach"
    ]
    beach_name_select = st.selectbox("Select a popular California beach:", california_beaches)
    if st.button("Get Forecast for Selected Beach", type="primary"):
        st.session_state.run_forecast = True
        st.session_state.beach_name = beach_name_select

# --- Forecast and Prediction Display ---
if "run_forecast" in st.session_state and st.session_state.run_forecast:
    with st.spinner(f"Fetching data and generating prediction for {st.session_state.beach_name}..."):
        # Fetch the 7-day forecast data
        forecast_df = kookpy.get_surf_forecast_by_name(st.session_state.beach_name)

        if forecast_df.empty:
            st.error("Could not find forecast for that location. Please try another name or check your internet connection.")
            st.session_state.run_forecast = False
        else:
            try:
                # Add a column for the predicted score
                forecast_df['wave_quality_score'] = forecast_df.apply(
                    lambda row: kookpy.predict_surf_quality(row), axis=1
                )
            except Exception as e:
                st.error(f"Prediction failed. Have you trained your model by running 'model_trainer.py'? Error: {e}")
                st.session_state.run_forecast = False
                st.stop()

            # Convert wave height from meters to feet for plotting
            forecast_df['swell_wave_height_ft'] = forecast_df['swell_wave_height'] * 3.281

            st.success(f"Forecast and prediction for {st.session_state.beach_name} ready.")
            st.markdown("---")

            # --- Visualization ---
            st.subheader("7-Day Surf Forecast and Predicted Quality")

            # Create interactive Plotly figures with blue/purple gradient
            fig_wave = px.scatter(
                forecast_df,
                x='time',
                y='swell_wave_height_ft',
                color='wave_quality_score',
                color_continuous_scale=px.colors.sequential.Bluyl,
                labels={'swell_wave_height_ft': 'Swell Wave Height (ft)', 'wave_quality_score': 'Quality Score'},
                hover_data={
                    'swell_wave_height_ft': ':.2f',
                    'swell_wave_period': ':.2f',
                    'wind_speed_10m': ':.2f',
                    'time': '|%B %d, %Y (%H:%M)'
                }
            )

            fig_wave.update_traces(marker=dict(size=10), mode='lines+markers', line=dict(color='#8A2BE2')) # A cool purple color
            fig_wave.update_layout(coloraxis_colorbar=dict(title="Quality Score"))

            fig_wind = px.line(
                forecast_df,
                x='time',
                y='wind_speed_10m',
                labels={'wind_speed_10m': 'Wind Speed (km/h)'},
            )
            fig_wind.update_traces(line=dict(color='#00BFFF', dash='dot')) # Deep sky blue for contrast

            # Create subplots to combine the figures
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15,
                                subplot_titles=(f"Swell Wave Height and Predicted Quality for {st.session_state.beach_name}", "Wind Speed Forecast"))

            # Add wave trace to the top subplot
            for trace in fig_wave.data:
                fig.add_trace(trace, row=1, col=1)

            # Add wind trace to the bottom subplot
            for trace in fig_wind.data:
                fig.add_trace(trace, row=2, col=1)

            # Update subplot titles and labels
            fig.update_yaxes(title_text="Swell Wave Height (ft)", row=1, col=1)
            fig.update_yaxes(title_text="Wind Speed (km/h)", row=2, col=1)
            fig.update_xaxes(title_text="Date and Time", row=2, col=1)
            fig.update_layout(hovermode="x unified")
            fig.update_layout(height=800)

            st.plotly_chart(fig, use_container_width=True)

            # --- Data Table ---
            st.subheader("Raw Forecast Data")
            st.dataframe(forecast_df[['time', 'swell_wave_height_ft', 'swell_wave_period', 'wind_speed_10m', 'wind_direction_10m', 'wave_quality_score']])
