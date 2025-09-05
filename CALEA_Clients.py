# Script to map the CALEA clients for project planning
import pandas as pd
import folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import requests

# Load the CSV file. Adjust the file path as necessary.

df = pd.read_csv("NPI active client list 4.2.25.csv")
df.head()  # Display the first few rows to check the data
df.columns # Display the column names to understand the structure

# Assuming your CSV has columns named 'Address', 'City', 'State', and 'Zip'
# If the column names differ, please adjust these accordingly.
#df["Full Address"] = df["Parent Organization Info Primary Address Line1"] + ", " + df["Parent Organization Info Primary Address City"] + ", " + df["Parent Organization Info Primary Address State Code"] + " " + df["Parent Organization Info Primary Address Zipcode"].astype(str)
df["City Query"] = (
    df["Parent Organization Info Primary Address City"] + ", " +
    df["Parent Organization Info Primary Address State Code"] + " " +
    df["Parent Organization Info Primary Address Zipcode"].astype(str)
)
# Define your Mapbox API key
MAPBOX_API_KEY = 'pk.eyJ1IjoiY2RvbGx5IiwiYSI6ImNtOTBqbGhtczBmcXQyanBxOXh5bXVpdG0ifQ.zUjqiwxV7l2ti5M87nt_zg'

def geocode_address(address):
    base_url = "https://api.mapbox.com/geocoding/v5/mapbox.places/{}.json".format(address)
    params = {
        "access_token": MAPBOX_API_KEY,
        "limit": 1
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if "features" in data and data["features"]:
            coords = data["features"][0]["geometry"]["coordinates"]
            return pd.Series([coords[1], coords[0]])  # lat, lon
        else:
            print(f"No geocoding result for: {address}")
            return pd.Series([None, None])
    except Exception as e:
        print(f"Error geocoding address '{address}': {e}")
        return pd.Series([None, None])

geocode_address = RateLimiter(geocode_address, min_delay_seconds=0.1)
#df[["Latitude", "Longitude"]] = df["Full Address"].apply(lambda x: geocode_address(x)).apply(pd.Series)
df[["Latitude", "Longitude"]] = df["City Query"].apply(lambda x: geocode_address(x)).apply(pd.Series)
failed = df[df["Latitude"].isna()]
failed.to_csv("failed_geocodes.csv", index=False)
df.to_csv("geocoded_results.csv", index=False)

# Creating the Map ###########################################################################################################
import folium
from folium.plugins import MarkerCluster
from folium.plugins import FeatureGroupSubGroup

# Create base map
m = folium.Map(location=[39.5, -98.35], zoom_start=4, tiles="CartoDB positron")

# Clean and bin size
df_map = df.dropna(subset=["Latitude", "Longitude"]).copy()
df_map["Personnel"] = pd.to_numeric(df_map["Extension Program Authorized Full Time Sworn Personnel"], errors="coerce").fillna(0)

def size_bin(p):
    if p < 25:
        return "Small (<25)"
    elif p < 100:
        return "Medium (25-99)"
    else:
        return "Large (100+)"
df_map["Size Group"] = df_map["Personnel"].apply(size_bin)

# Unique values
size_groups = df_map["Size Group"].unique()
program_types = df_map["Program Type"].dropna().unique()

# Master control group
master_group = folium.FeatureGroup(name="All Agencies").add_to(m)

# Generate subgroup layers
layer_dict = {}

for size in size_groups:
    for ptype in program_types:
        layer_name = f"{size} - {ptype}"
        subgroup = folium.FeatureGroup(name=layer_name)
        layer_dict[(size, ptype)] = subgroup
        m.add_child(subgroup)

# Add markers to appropriate group
for _, row in df_map.iterrows():
    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=6,
        fill=True,
        fill_color="#3186cc",
        fill_opacity=0.7,
        tooltip=row.get("Parent Organization Info Name", "Unknown")
    ).add_to(m)
    
    
import pandas as pd

# Safely extract award date with fallback
award_date_raw = row.get("Agency Award Date", None)

# Format award date or label as "Self-Assessment"
if pd.isna(award_date_raw):
    award_display = "Self-Assessment"
else:
    try:
        award_display = pd.to_datetime(award_date_raw).strftime("%Y-%m-%d")
    except:
        award_display = str(award_date_raw)  # Fallback if not a real date

popup_text = (
    f"<b>{agency}</b><br>"
    f"{city}, {state}<br>"
    f"Program Type: {ptype}<br>"
    f"Sworn Personnel: {row['Personnel']}<br>"
    f"Last Award Date: {award_display}"
)


if (size, ptype) in layer_dict:
        folium.CircleMarker(
    location=[row["Latitude"], row["Longitude"]],
    radius=6,
    color='gray',
    fill=True,
    fill_color='#3186cc',
    fill_opacity=0.7,
    popup=popup_text,
    tooltip=tooltip_text
).add_to(layer_dict[(size, ptype)])

# Add controls
folium.LayerControl(collapsed=False).add_to(m)
m.save("calea_clients_filtered_map.html")