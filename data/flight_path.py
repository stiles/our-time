import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# Step 1: Load the CSV file
file_path = "./data/CI7_385dbc13.csv"  # Replace with your file path
data = pd.read_csv(file_path)

# Step 2: Parse positions into (lon, lat) and normalize longitudes
data['Position'] = data['Position'].str.replace('"', '')  # Remove quotes
data['Coordinates'] = data['Position'].apply(lambda x: tuple(map(float, x.split(',')))[::-1])

# Normalize longitudes to [-180, 180]
def normalize_longitude(lon):
    return lon - 360 if lon > 180 else lon

data['Normalized'] = data['Coordinates'].apply(lambda x: (normalize_longitude(x[0]), x[1]))

# Step 3: Split LineString at the International Date Line
def split_at_dateline(coords):
    """Split a LineString at the International Date Line."""
    lines = []
    current_line = [coords[0]]
    for i in range(1, len(coords)):
        lon1, lat1 = coords[i - 1]
        lon2, lat2 = coords[i]
        # Detect crossing the International Date Line
        if abs(lon2 - lon1) > 180:
            # Calculate approximate crossing latitude
            dateline_lat = lat1 + (lat2 - lat1) * (180 - abs(lon1)) / abs(lon2 - lon1)
            # Add two points to "break" at the dateline
            current_line.append((180 if lon1 < 0 else -180, dateline_lat))
            lines.append(LineString(current_line))
            current_line = [(-180 if lon2 > 0 else 180, dateline_lat), (lon2, lat2)]
        else:
            current_line.append((lon2, lat2))
    lines.append(LineString(current_line))
    return lines

# Generate split lines
coords = data['Normalized'].tolist()
split_lines = split_at_dateline(coords)

# Step 4: Create a GeoDataFrame and export as GeoJSON
gdf = gpd.GeoDataFrame({'geometry': split_lines}, crs="EPSG:4326")
geojson_output = "./data/flight_path_split.geojson"
gdf.to_file(geojson_output, driver="GeoJSON")
print(f"GeoJSON saved to {geojson_output}")

# Step 5: Plot the split path for verification
fig, ax = plt.subplots(figsize=(12, 6), subplot_kw={'projection': ccrs.PlateCarree()})
ax.set_title("Flight Path: LA to Taipei (Split at Date Line)", fontsize=16)

# Add background features
ax.add_feature(cfeature.LAND, color='lightgray')
ax.add_feature(cfeature.OCEAN, color='lightblue')
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.gridlines(draw_labels=True)

# Plot each split segment
for line in split_lines:
    ax.plot(*line.xy, linewidth=2, color='red', transform=ccrs.PlateCarree())

plt.show()
