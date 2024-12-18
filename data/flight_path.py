import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# Step 1: Load the CSV file
file_path = "./data/flightaware_flight_path.csv"  # Replace with your file path
data = pd.read_csv(file_path)

# Step 2: Parse Latitude and Longitude into (lon, lat) order
data['Coordinates'] = list(zip(data['Longitude'], data['Latitude']))

# Step 3: Handle the Date Line wrap
def split_at_dateline(coords):
    """Split a list of coordinates at the International Date Line."""
    lines = []
    current_line = [coords[0]]
    for i in range(1, len(coords)):
        lon1, lat1 = coords[i - 1]
        lon2, lat2 = coords[i]
        # If the difference in longitude is > 180°, split the line
        if abs(lon2 - lon1) > 180:
            if len(current_line) > 1:  # Add only valid lines
                lines.append(LineString(current_line))
            current_line = [(lon2, lat2)]  # Start a new line
        else:
            current_line.append((lon2, lat2))
    # Add the final line if valid
    if len(current_line) > 1:
        lines.append(LineString(current_line))
    return lines

# Step 4: Split the coordinates into separate lines
coords = data['Coordinates'].tolist()
split_lines = split_at_dateline(coords)

# Step 5: Validate and Export Each Line
print(f"Number of split lines: {len(split_lines)}")

def save_geojson(line, output_path, name):
    """Validate and save LineString to GeoJSON."""
    if line.is_valid and not line.is_empty:
        print(f"{name} - Valid Geometry Length: {len(line.coords)}")
        gdf = gpd.GeoDataFrame({'geometry': [line]}, crs="EPSG:4326")
        gdf.to_file(output_path, driver="GeoJSON")
        print(f"{name} saved successfully: {output_path}")
    else:
        print(f"{name} is invalid or empty.")

# Save Leg 1 and Leg 2
save_geojson(split_lines[0], "./data/flight_path_leg1.geojson", "Leg 1")
if len(split_lines) > 1:
    save_geojson(split_lines[1], "./data/flight_path_leg2.geojson", "Leg 2")

# Step 6: Plot both legs to verify
fig, ax = plt.subplots(figsize=(12, 6), subplot_kw={'projection': ccrs.PlateCarree()})
ax.set_title("Flight Path: LA to Taipei (Split at Date Line)", fontsize=16)

# Add background features
ax.add_feature(cfeature.LAND, color='lightgray')
ax.add_feature(cfeature.OCEAN, color='lightblue')
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.gridlines(draw_labels=True)

# Plot available lines
ax.plot(*split_lines[0].xy, color='blue', linewidth=2, label="Leg 1", transform=ccrs.PlateCarree())
if len(split_lines) > 1:
    ax.plot(*split_lines[1].xy, color='red', linewidth=2, label="Leg 2", transform=ccrs.PlateCarree())

plt.legend()
plt.show()
