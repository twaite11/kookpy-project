from kookpy import get_surf_forecast_by_name, plot_surf_data

location_name = "Laguna Beach"

print(f"Fetching surf data for {location_name}...")
surf_data = get_surf_forecast_by_name(location_name)

if not surf_data.empty:
    print("Data fetched successfully. Plotting now.")
    plot_surf_data(surf_data, location_name)
else:
    print("Failed to fetch data. Please check the beach name or network connection.")