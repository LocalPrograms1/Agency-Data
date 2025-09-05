import pandas as pd
import googlemaps
import time
from gmplot import GoogleMapPlotter
import folium

# --- CONFIGURATION ---
# CSV file paths (adjust if necessary)
INPUT_CSV = "NPI active client list 4.2.25.csv"
FAILED_CSV = "failed_geocodes_google.csv"
RESULTS_CSV = "geocoded_results_google.csv"
OUT_HTML = "calea_clients_filtered_map_google.html"

# Your Google API key (used for geocoding)
GOOGLE_API_KEY = 'AIzaSyBSiuT4KVEpHNR_MAiYZJryOpHCTkPIbcY'

# Initialize the googlemaps client
gmaps_client = googlemaps.Client(key=GOOGLE_API_KEY)

# Load CSV data
df = pd.read_csv(INPUT_CSV)
df.head()  # Display a few rows for verification
df.columns  # Verify column names

# Create a city-level query string
df["City Query"] = (
    df["Parent Organization Info Primary Address City"] + ", " +
    df["Parent Organization Info Primary Address State Code"] + " " +
    df["Parent Organization Info Primary Address Zipcode"].astype(str)
)

# --- GEOCODING FUNCTION USING GOOGLE ---
def geocode_address(address):
    try:
        geocode_result = gmaps_client.geocode(address)
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return pd.Series([location['lat'], location['lng']])
        else:
            print(f"No geocoding result for: {address}")
            return pd.Series([None, None])
    except Exception as e:
        print(f"Error geocoding address '{address}': {e}")
        return pd.Series([None, None])

# Apply geocoding.
# To stay under the rate limit, we pause between calls.
lats, lons = [], []
for address in df["City Query"]:
    lat, lon = geocode_address(address)
    lats.append(lat)
    lons.append(lon)
    time.sleep(0.1)  # Adjust delay if needed

df["Latitude"] = lats
df["Longitude"] = lons

# Save failed geocodes
failed = df[df["Latitude"].isna()]
failed.to_csv(FAILED_CSV, index=False)
df.to_csv(RESULTS_CSV, index=False)

# Prepare map data (drop missing coordinates)
df_map = df.dropna(subset=["Latitude", "Longitude"]).copy()


# Compute the map center as the average latitude and longitude
center_lat = df_map["Latitude"].mean()
center_lon = df_map["Longitude"].mean()

#------------------------------------------------------------------------------------------#

# Create the Folium map using the CartoDB Positron basemap
m = folium.Map(location=[center_lat, center_lon], zoom_start=4, tiles="CartoDB positron")

# Define a mapping for Program Type to marker colors (supported colors for folium.Icon)
color_map = {
    "Law Enforcement Accreditation": "blue",
    "Communications Accreditation": "green",
    "Training Academy Accreditation": "red"
}
default_color = "gray"  # Fallback color if Program Type isn't in mapping

# Create two feature groups: one for rows with award data and one for missing award data.
award_present = folium.FeatureGroup(name="Award Date Present")
award_missing = folium.FeatureGroup(name="Award Date Missing")

# Add markers for each geocoded location to the appropriate feature group and color code by Program Type.
# Add markers for each geocoded location directly to the map, with icon determined by award date.
for _, row in df_map.iterrows():
    lat = row["Latitude"]
    lon = row["Longitude"]
    program_type = row.get("Program Type", "Unknown")
    marker_color = color_map.get(program_type, default_color)
    popup_text = (
        f"{row['Parent Organization Info Name']}<br>"
        f"Sworn Personnel: {row['Extension Program Authorized Full Time Sworn Personnel']}<br>"
        f"Program Type: {program_type}"
    )
    # Select icon based on the existence of the award date:
    if pd.isna(row.get("Agency Award Date (Most Recent)")):
        icon = folium.Icon(color=marker_color, icon='times', prefix='fa')
    else:
        icon = folium.Icon(color=marker_color, icon='check', prefix='fa')
    folium.Marker(
        [lat, lon],
        popup=popup_text,
        icon=icon
    ).add_to(m)
    
folium.Marker(
    [lat, lon],
    popup=popup_text,
    icon=folium.Icon(color=marker_color, icon='location-pin', prefix='fa')
).add_to(m)
# Use explicit dictionary lookups for clarity:
le_color = color_map["Law Enforcement Accreditation"]
com_color = color_map["Communications Accreditation"]
ta_color = color_map["Training Academy Accreditation"]

legend_html = '''
<div style="
    position: fixed; 
    top: 50px; right: 50px; width: 300px; height: 250px; 
    border:2px solid grey; z-index:9999; font-size:14px;
    background-color: gray;
    opacity: 0.9;
    padding: 10px;
">
<b>Legend</b><br>
&nbsp;<i class="fa fa-location-pin fa-2x" style="color: {le_color};"></i>&nbsp;Law Enforcement Accreditation<br>
&nbsp;<i class="fa fa-location-pin fa-2x" style="color: {com_color};"></i>&nbsp;Communications Accreditation<br>
&nbsp;<i class="fa fa-location-pin fa-2x" style="color: {ta_color};"></i>&nbsp;Training Academy Accreditation<br>
&nbsp;<i class="fa fa-check fa-2x" style="color: white;"></i>&nbsp;Accredited Agency<br>
&nbsp;<i class="fa fa-times fa-2x" style="color: white;"></i>&nbsp;In Self-Assessment<br>
</div>
'''.format(
    le_color=le_color,
    com_color=com_color,
    ta_color=ta_color
)
m.get_root().html.add_child(folium.Element(legend_html))
# Save the interactive map to an HTML file.
m.save(OUT_HTML)
print(f"Map saved to {OUT_HTML}")
