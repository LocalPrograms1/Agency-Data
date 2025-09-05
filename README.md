# CALEA Agencies Dashboard

An interactive web dashboard built with Dash/Plotly to visualize CALEA (Commission on Accreditation for Law Enforcement Agencies) accredited agencies across the United States.

## Features

- **Interactive Map**: Displays all agencies on a map with different colors for program types
- **Advanced Filtering**: Filter agencies by program type, size category, and award status
- **Summary Statistics**: Real-time statistics with hover effects showing total agencies, accredited vs self-assessment
- **Interactive Data Table**: 
  - Sortable columns (single and multi-column sorting)
  - Built-in search and filtering for each column
  - Pagination with 20 rows per page
  - Responsive design with horizontal scrolling
- **Modern Typography**: Uses Fira Code for headers/numbers and Inter for body text
- **Responsive Design**: Works on desktop and mobile devices

## Program Types

- **Law Enforcement Accreditation** (Blue)
- **Communications Accreditation** (Orange)
- **Training Academy Accreditation** (Green)

## Size Categories

- **Small**: <25 sworn personnel
- **Medium**: 25-99 sworn personnel  
- **Large**: 100+ sworn personnel

## Running Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser to `http://localhost:8050`

## Deployment

### Posit Connect

1. Ensure your `requirements.txt` includes all dependencies
2. Upload the project files to Posit Connect
3. Configure the deployment settings
4. The app will be accessible via your Posit Connect URL

### Heroku

1. Create a `Procfile`:
```
web: gunicorn app:server
```

2. Deploy to Heroku using Git or GitHub integration

## Files

- `app.py` - Main Dash application
- `geocoded_results_google.csv` - Source data with geocoded agency locations
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Data Source

The dashboard uses data from `geocoded_results_google.csv` which contains:
- Agency names and addresses
- Geocoded latitude/longitude coordinates
- Program types and personnel counts
- Accreditation award dates and status