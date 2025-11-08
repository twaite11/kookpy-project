import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import kookpy
from datetime import datetime, timedelta
import base64
import numpy as np

# page config
st.set_page_config(layout="wide", page_title="Kookpy AI Surf Forecast")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 5px;
        font-size: 16px;
        color: #c9d1d9;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #232d39;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def create_logo_svg():
    """Generates an abstract blue and purple wave-like logo."""
    return f"""
    <svg width="60" height="60" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="waveGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#61A4D3;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#A855F7;stop-opacity:1" />
        </linearGradient>
      </defs>
      <path d="M10 50 Q30 30 50 50 T90 50" stroke="url(#waveGradient)" stroke-width="10" fill="none" stroke-linecap="round"/>
    </svg>
    """


def create_wave_icon(height_ft):
    """Generates an eye-catching SVG string for a wave height icon."""
    scaled_height = min(1.0, height_ft / 10.0)

    return f"""
    <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <style>
            @keyframes wave-motion {{
                0% {{ transform: scaleY(1) translateY(0); }}
                50% {{ transform: scaleY(1.2) translateY(-5px); }}
                100% {{ transform: scaleY(1) translateY(0); }}
            }}
            .wave-body {{
                fill: #61A4D3;
                animation: wave-motion 2s infinite cubic-bezier(0.4, 0, 0.6, 1);
            }}
        </style>
        <path class="wave-body" d="M0,50 Q25,25 50,50 T100,50" style="transform-origin: 50% 50%; transform: scaleY({0.5 + scaled_height/2});"/>
    </svg>
    """


def create_wind_icon(speed, direction):
    """Generates an animated SVG string for a wind direction icon."""
    animation_duration = max(0.5, 2 - (speed / 30))
    rotation = direction + 180
    return f"""
    <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <style>
            .wind-arrow {{
                fill: #61A4D3;
                transform-origin: 50% 50%;
                animation: wind-flow {animation_duration}s infinite linear;
            }}
            @keyframes wind-flow {{
                0% {{ transform: rotate({rotation}deg) scale(1); }}
                50% {{ transform: rotate({rotation}deg) scale(1.1); }}
                100% {{ transform: rotate({rotation}deg) scale(1); }}
            }}
        </style>
        <path class="wind-arrow" d="M50,15 L60,35 L50,30 L40,35 Z" />
        <circle cx="50" cy="50" r="30" fill="none" stroke="#61A4D3" stroke-width="2" />
        <path d="M50,20 L50,30" stroke="#61A4D3" stroke-width="2"/>
        <path d="M50,70 L50,80" stroke="#61A4D3" stroke-width="2"/>
        <path d="M20,50 L30,50" stroke="#61A4D3" stroke-width="2"/>
        <path d="M70,50 L80,50" stroke="#61A4D3" stroke-width="2"/>
    </svg>
    """


def create_viridis_color(normalized_score):
    """Generates a hex color from a Viridis-like gradient."""
    # define the pattern -- grab from https://cran.r-project.org/web/packages/viridis/vignettes/intro-to-viridis.html
    colors = ['#440154', '#472f7d', '#3e6a8e', '#29918c',
              '#33b479', '#9fce25', '#fddc24', '#f6e812']
    index = int(normalized_score * (len(colors) - 1))
    return colors[index]


def create_score_icon(score, max_score=10):
    """Generates an SVG string for a circular score meter with color."""
    normalized_score = max(0, min(1, score / max_score))
    progress_color = create_viridis_color(normalized_score)
    circumference = 2 * np.pi * 40
    stroke_dashoffset = circumference * (1 - normalized_score)

    return f"""
    <svg width="400" height="400" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="50" r="45" stroke="#444" stroke-width="10" fill="none"/>
      <circle cx="50" cy="50" r="45" stroke="{progress_color}" stroke-width="10" fill="none"
              stroke-dasharray="{circumference}" stroke-dashoffset="{stroke_dashoffset}"
              transform="rotate(-90 50 50)"/>
      <text x="50" y="50" font-size="30" fill="#c9d1d9" text-anchor="middle" alignment-baseline="middle" style="font-family: sans-serif;">{score:.1f}</text>
    </svg>
    """


def create_tide_icon():
    """Generates a static SVG icon for tide data."""
    return f"""
    <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <path d="M10,50 Q25,40 50,50 T90,50" fill="none" stroke="#61A4D3" stroke-width="3" />
        <path d="M50,50 L50,80" stroke="#61A4D3" stroke-width="3" />
        <path d="M45,80 L55,80" stroke="#61A4D3" stroke-width="3" />
        <path d="M50,50 L40,40 L60,40 L50,50 Z" fill="#61A4D3" />
    </svg>
    """


def create_tide_data_html(tide_data):
    """Creates an HTML string to display tide data."""
    if not tide_data:
        return "Tide data not available."

    html = "<div style='font-size: 14px;'>"

    if 'next_high_tide' in tide_data:
        high_tide_height = tide_data['next_high_tide']['height_m'] * 3.281
        high_tide_time = tide_data['next_high_tide']['time']
        html += f"<p style='margin: 0;'>High: {high_tide_time} ({high_tide_height:.1f} ft)</p>"

    if 'next_low_tide' in tide_data:
        low_tide_height = tide_data['next_low_tide']['height_m'] * 3.281
        low_tide_time = tide_data['next_low_tide']['time']
        html += f"<p style='margin: 0;'>Low: {low_tide_time} ({low_tide_height:.1f} ft)</p>"

    html += "</div>"
    return html


def image_to_base64(svg_string):
    """Converts a string of SVG to a base64-encoded URI."""
    encoded = base64.b64encode(svg_string.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{encoded}"


def create_score_legend():
    """Generates the AI quality score legend using Streamlit components."""
    st.markdown("### AI Wave Quality Score Explained")
    st.markdown("This is a prediction of wave quality on a scale of 1-10. It is a beta feature trained on historical data and is constantly learning.")

    # the bar -- make gradient
    st.markdown(
        """
        <div style="
            background: linear-gradient(to right, #440154, #472f7d, #3e6a8e, #29918c, #33b479, #9fce25, #fddc24, #f6e812);
            height: 20px;
            width: 100%;
            border-radius: 5px;
            margin-right: 15px;
        "></div>
        """,
        unsafe_allow_html=True
    )

    # qualitative scores
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(
            "<p style='font-size: 12px; text-align: center; color: #440154;'><b>1</b><br>(Terrible)</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(
            "<p style='font-size: 12px; text-align: center; color: #29918c;'><b>5</b><br>(Decent)</p>", unsafe_allow_html=True)
    with col3:
        st.markdown(
            "<p style='font-size: 12px; text-align: center; color: #33b479;'><b>6</b><br>(Good)</p>", unsafe_allow_html=True)
    with col4:
        st.markdown(
            "<p style='font-size: 12px; text-align: center; color: #fddc24;'><b>8</b><br>(Great)</p>", unsafe_allow_html=True)
    with col5:
        st.markdown(
            "<p style='font-size: 12px; text-align: center; color: #f6e812;'><b>10</b><br>(All time)</p>", unsafe_allow_html=True)


# title and description
col_logo, col_title = st.columns([1, 10])
with col_logo:
    st.image(image_to_base64(create_logo_svg()), width=60)
with col_title:
    st.title("Kookpy AI Surf Forecast")
    st.markdown("### Powered by the Open-Meteo API and TensorFlow")

# USER INPUT SECTION
st.markdown("---")
tabs = st.tabs(["Search by Name", "Select from List"])

with tabs[0]:
    beach_name_input = st.text_input(
        "Enter a beach name:", "Laguna Beach", help="e.g., Laguna Beach, Huntington Beach, Waikiki")
    if st.button("Get Forecast & Prediction", type="primary"):
        if not beach_name_input:
            st.error("Please enter a valid beach name.")
        else:
            st.session_state.run_forecast = True
            st.session_state.beach_name = beach_name_input

with tabs[1]: # this is dog, need to create a separate library somewhere yeeesh
    california_beaches = [
        "Huntington Beach", "Malibu", "Santa Cruz", "La Jolla", "Trestles",
        "Steamer Lane", "Rincon", "Newport Beach", "Pacifica State Beach", "Point Dume",
        "Zuma Beach", "El Porto", "Venice Beach", "Manhattan Beach", "Hermosa Beach",
        "Redondo Beach", "Torrance Beach", "Cabrillo Beach", "Dana Point", "San Onofre",
        "Swami's", "Cardiff Reef", "Ponto Beach", "Oceanside Harbor", "Black's Beach",
        "Del Mar", "Encinitas", "Solana Beach", "Mission Beach", "Ocean Beach",
        "Sunset Cliffs", "Imperial Beach", "Fort Point", "Ocean Beach, San Francisco",
        "Half Moon Bay", "Mavericks", "Bolinas", "Stinson Beach", "Montara",
        "Cowell's Beach", "Pleasure Point", "Capitola", "Seabright Beach", "Manresa State Beach",
        "Moss Landing", "Marina State Beach", "Carmel Beach", "Asilomar State Beach",
        "Morro Bay", "Pismo Beach", "Avila Beach", "Cayucos", "Cambria",
        "Point Conception", "Jalama Beach", "Refugio State Beach", "El Capitan State Beach",
        "Gaviota State Park", "Carpinteria", "Summerland", "Leadbetter Beach", "Campus Point",
        "Isla Vista", "Mondos", "Emma Wood", "C Street, Ventura", "Silver Strand",
        "Leo Carrillo State Park", "El Matador State Beach", "Topanga State Beach",
        "Surfrider Beach", "County Line", "Zuma", "Oxnard Shores", "Ventura Point",
        "Rincon Point", "Pismo State Beach", "Grover Beach", "Santa Monica State Beach",
        "Dockweiler Beach", "Manhattan Beach Pier", "Venice Breakwater", "San Clemente Pier",
        "Doheny State Beach", "Salt Creek", "Strands Beach", "Thalia Street",
        "Brooks Street", "Main Beach, Laguna", "Table Rock Beach", "Aliso Beach",
        "Laguna Niguel", "Dana Strands", "San Clemente", "Huntington Cliffs",
        "Seal Beach", "Alamitos Bay", "Belmont Shore", "Long Beach", "Point Mugu",
        "Morro Strand State Beach", "Sunset Beach, Orange County", "Bolsa Chica State Beach",
        "San Elijo State Beach"
    ]
    beach_name_select = st.selectbox(
        "Select a popular California beach:", california_beaches)
    if st.button("Get Forecast for Selected Beach", type="primary"):
        st.session_state.run_forecast = True
        st.session_state.beach_name = beach_name_select

#Forecast and Prediction Display
if "run_forecast" in st.session_state and st.session_state.run_forecast:
    with st.spinner(f"Fetching data and generating prediction for {st.session_state.beach_name}..."):
        # Get location coordinates first
        coords = kookpy.geocode_location(st.session_state.beach_name)
        if not coords:
            st.error("Could not find coordinates for that location.")
            st.session_state.run_forecast = False
            st.stop()

        # get data using the coordinates
        forecast_df = kookpy.get_surf_forecast_by_name(
            st.session_state.beach_name)

        if forecast_df.empty:
            st.error(
                "Could not find forecast for that location. Please try another name or check your internet connection.")
            st.session_state.run_forecast = False
        else:
            try:
                # Ensure the DataFrame has the columns needed for prediction
                required_features = [
                    'swell_wave_height', 'swell_wave_period', 'wind_speed_10m', 'sea_level_height_msl']
                if not all(feature in forecast_df.columns for feature in required_features):
                    st.error(
                        "Forecast data is missing required features for AI prediction.")
                    st.session_state.run_forecast = False
                    st.stop()

                forecast_df['wave_quality_score'] = forecast_df.apply(
                    lambda row: kookpy.predict_surf_quality(row), axis=1
                )
            except Exception as e:
                st.error(
                    f"Prediction failed. Have you trained your model by running 'model_trainer.py'? Error: {e}")
                st.session_state.run_forecast = False
                st.stop()

            # get tide data for the next 48 hours to find high/low tides
            tide_data = kookpy.fetch_tide_data(coords['latitude'], coords['longitude'], datetime.now(
            ).date().strftime('%Y-%m-%d'), (datetime.now().date() + timedelta(days=2)).strftime('%Y-%m-%d'))

            forecast_df['swell_wave_height_ft'] = forecast_df['swell_wave_height'] * 3.281
            st.success(
                f"Forecast and prediction for {st.session_state.beach_name} ready.")
            st.markdown("---")

            # Current Conditions Summary
            st.subheader("Current Conditions")
            if not forecast_df.empty:
                now_df = forecast_df.iloc[0]

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown(f"**AI QUALITY SCORE**")
                    score_icon_svg = create_score_icon(
                        now_df['wave_quality_score'])
                    st.image(image_to_base64(score_icon_svg), width=200)

                with col2:
                    st.markdown(f"**CURRENT WAVE HEIGHT**")
                    st.markdown(
                        f"<p style='font-size: 30px; margin: 0;'>{now_df['swell_wave_height_ft']:.1f} ft</p>", unsafe_allow_html=True)
                    wave_icon_svg = create_wave_icon(
                        now_df['swell_wave_height_ft'])
                    st.image(image_to_base64(wave_icon_svg), width=100)

                with col3:
                    st.markdown(f"**CURRENT WIND**")
                    st.markdown(
                        f"<p style='font-size: 30px; margin: 0;'>{now_df['wind_speed_10m']:.1f} km/h</p>", unsafe_allow_html=True)
                    wind_icon_svg = create_wind_icon(
                        now_df['wind_speed_10m'], now_df['wind_direction_10m'])
                    st.image(image_to_base64(wind_icon_svg), width=100)

                with col4:
                    st.markdown(f"**TIDE**")
                    if tide_data and 'next_high_tide' in tide_data:
                        st.markdown(
                            f"<p style='font-size: 30px; margin: 0;'>{tide_data['next_high_tide']['height_m'] * 3.281:.1f} ft</p>", unsafe_allow_html=True)
                        tide_data_html = f"<div style='font-size: 14px;'><b>Next Tides:</b><p style='margin: 0;'>High: {tide_data['next_high_tide']['time']} ({tide_data['next_high_tide']['height_m'] * 3.281:.1f} ft)</p></div>"
                        if 'next_low_tide' in tide_data:
                            tide_data_html += f"<p style='margin: 0;'>Low: {tide_data['next_low_tide']['time']} ({tide_data['next_low_tide']['height_m'] * 3.281:.1f} ft)</p>"
                        st.markdown(tide_data_html, unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f"<p style='font-size: 30px; margin: 0;'>N/A</p>", unsafe_allow_html=True)
                        st.write("Tide data not available.")
                    tide_icon_svg = create_tide_icon()
                    st.image(image_to_base64(tide_icon_svg), width=100)

            st.markdown("---")
            st.subheader("7-Day Forecast")

            # --- AI Quality Score Explanation ---
            create_score_legend()

            # --- Visualization ---
            forecast_df_3hr = forecast_df[forecast_df['time'].dt.hour % 3 == 0]

            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                                subplot_titles=(f"Swell Wave Height and Predicted Quality for {st.session_state.beach_name}", "Wind Speed Forecast", "Tide Forecast"))

            # --- Wave Height Bar Chart ---
            fig.add_trace(go.Bar(
                x=forecast_df_3hr['time'],
                y=forecast_df_3hr['swell_wave_height_ft'],
                marker_color=forecast_df_3hr['wave_quality_score'],
                marker_colorscale='Viridis',
                marker_cmin=1,  # Set the minimum value for the color scale
                marker_cmax=10,
                hovertemplate="<b>%{x|%b %d, %I:%M %p}</b><br>Wave Height: %{y:.2f} ft<br>Quality Score: %{marker.color:.1f}<extra></extra>",
                name="Wave Height",
                showlegend=False
            ), row=1, col=1)

            # vertical dashed lines for each day and date headers, this is so broken but not high prio
            dates = pd.to_datetime(forecast_df['time']).dt.date.unique()
            for i, date in enumerate(dates):
                date_str = date.strftime('%Y-%m-%d')
                fig.add_vline(x=date_str, line_width=1, line_dash="dash",
                              line_color="white", opacity=0.5, row=1, col=1)
                fig.add_vline(x=date_str, line_width=1, line_dash="dash",
                              line_color="white", opacity=0.5, row=2, col=1)
                fig.add_vline(x=date_str, line_width=1, line_dash="dash",
                              line_color="white", opacity=0.5, row=3, col=1)

                if i < len(dates) - 1:
                    mid_point = date + (dates[i+1] - date) / 2
                    fig.add_annotation(
                        x=mid_point,
                        y=-1.05,
                        text=date.strftime('%b %d'),
                        xref="x",
                        yref="paper",
                        showarrow=False,
                        font=dict(color="#c9d1d9", size=16)
                    )

            # Wind Speed Line Chart
            fig.add_trace(go.Scatter(
                x=forecast_df['time'],
                y=forecast_df['wind_speed_10m'],
                mode='lines',
                name='Wind Speed (km/h)',
                line=dict(color='skyblue', dash='dot'),
                hovertemplate="<b>%{x|%b %d, %I:%M %p}</b><br>Wind Speed: %{y:.2f} km/h<extra></extra>"
            ), row=2, col=1)

            # Tide Chart
            fig.add_trace(go.Scatter(
                x=forecast_df['time'],
                y=forecast_df['sea_level_height_msl'],
                mode='lines',
                name='Sea Level Height',
                line=dict(color='cornflowerblue'),
                hovertemplate="<b>%{x|%b %d, %I:%M %p}</b><br>Tide: %{y:.2f} m<extra></extra>"
            ), row=3, col=1)

            high_tides = forecast_df[forecast_df['sea_level_height_msl'] == forecast_df['sea_level_height_msl'].rolling(
                window=3, center=True).max()].dropna()
            low_tides = forecast_df[forecast_df['sea_level_height_msl'] == forecast_df['sea_level_height_msl'].rolling(
                window=3, center=True).min()].dropna()

            fig.add_trace(go.Scatter(
                x=high_tides['time'],
                y=high_tides['sea_level_height_msl'],
                mode='markers',
                name='High Tide',
                marker=dict(symbol='triangle-up', size=10, color='red'),
                hovertemplate="<b>High Tide</b><br>Date: %{x|%b %d, %I:%M %p}</b><br>Height: %{y:.2f} m<extra></extra>"
            ), row=3, col=1)

            fig.add_trace(go.Scatter(
                x=low_tides['time'],
                y=low_tides['sea_level_height_msl'],
                mode='markers',
                name='Low Tide',
                marker=dict(symbol='triangle-down', size=10, color='white'),
                hovertemplate="<b>Low Tide</b><br>Date: %{x|%b %d, %I:%M %p}</b><br>Height: %{y:.2f} m<extra></extra>"
            ), row=3, col=1)

            fig.update_yaxes(title_text="Swell Wave Height (ft)", row=1, col=1)
            fig.update_yaxes(title_text="Wind Speed (km/h)", row=2, col=1)
            fig.update_yaxes(title_text="Sea Level (m)", row=3, col=1)
            fig.update_xaxes(title_text="Date and Time", row=3, col=1)
            fig.update_layout(hovermode="x unified",
                              plot_bgcolor='rgba(0,0,0,0)',
                              paper_bgcolor='rgba(0,0,0,0)',
                              font_color="#c9d1d9",
                              xaxis_gridcolor="#333",
                              yaxis_gridcolor="#333",)
            fig.update_layout(height=1000)

            fig.update_layout(
                title_text=f"Swell Wave Height and Predicted Quality for {st.session_state.beach_name}",
                legend=dict(orientation="h", yanchor="bottom",
                            y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig, use_container_width=True)
