# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a CALEA (Commission on Accreditation for Law Enforcement Agencies) client mapping and analysis project. The codebase consists of Python scripts for geocoding and visualizing CALEA-accredited agencies across the United States.

## Architecture

The project uses a data processing pipeline:
1. **Data Input**: CSV files containing agency information (`NPI active client list 4.2.25.csv`)
2. **Geocoding**: Two approaches implemented - Mapbox API (`CALEA_Clients.py`) and Google Maps API (`CALEA_Clients_2.py`)
3. **Visualization**: Interactive maps generated using Folium library
4. **Output**: HTML files with interactive maps and CSV files with geocoded results

### Key Components

- **CALEA_Clients.py**: Uses Mapbox geocoding API for address resolution and creates filtered, layered maps with size-based groupings
- **CALEA_Clients_2.py**: Uses Google Maps geocoding API with award status visualization and program type color coding

### Data Flow

1. Load agency data from CSV containing fields like:
   - Parent Organization Info Primary Address (City, State, Zipcode)
   - Extension Program Authorized Full Time Sworn Personnel
   - Program Type (Law Enforcement, Communications, Training Academy)
   - Agency Award Date

2. Generate city-level queries for geocoding APIs
3. Apply rate-limited geocoding to avoid API limits
4. Create interactive Folium maps with:
   - Size-based groupings (Small <25, Medium 25-99, Large 100+)
   - Program type color coding
   - Award status indicators

## Common Commands

This project uses standard Python execution - no build system or package management detected:

```bash
# Run the Mapbox-based geocoding and mapping
python CALEA_Clients.py

# Run the Google Maps-based geocoding and mapping  
python CALEA_Clients_2.py
```

## Dependencies

Required Python packages:
- pandas - Data manipulation
- folium - Interactive map generation
- geopy - Geocoding utilities (Nominatim, RateLimiter)
- googlemaps - Google Maps API client
- requests - HTTP requests for Mapbox API
- gmplot - Google Maps plotting (imported but not actively used)

## File Outputs

- `calea_clients_filtered_map.html` - Interactive map with layered agency data
- `calea_clients_filtered_map_google.html` - Google-based geocoded map
- `geocoded_results.csv` / `geocoded_results_google.csv` - Successful geocoding results
- `failed_geocodes.csv` / `failed_geocodes_google.csv` - Failed geocoding attempts

## API Keys

The scripts contain API keys for:
- Mapbox geocoding service
- Google Maps geocoding service

**Note**: API keys are currently hardcoded in the scripts and should be moved to environment variables for security.