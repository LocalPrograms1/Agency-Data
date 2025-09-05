import dash
from dash import dcc, html, Input, Output, callback, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# Load the data
try:
    df = pd.read_csv('geocoded_results_google.csv')
    print(f"Data loaded: {len(df)} rows")
except FileNotFoundError:
    print("Error: geocoded_results_google.csv not found")
    df = pd.DataFrame()

# Clean and prepare the data
if not df.empty:
    df = df.dropna(subset=['Latitude', 'Longitude'])
    df['Extension Program Authorized Full Time Sworn Personnel'] = pd.to_numeric(
        df['Extension Program Authorized Full Time Sworn Personnel'], errors='coerce'
    ).fillna(0)

    # Create size categories
    def get_size_category(personnel):
        if personnel < 25:
            return "Small (<25)"
        elif personnel < 100:
            return "Medium (25-99)"
        else:
            return "Large (100+)"

    df['Size Category'] = df['Extension Program Authorized Full Time Sworn Personnel'].apply(get_size_category)

    # Process award dates
    df['Agency Award Date (Most Recent)'] = pd.to_datetime(df['Agency Award Date (Most Recent)'], errors='coerce')
    df['Award Status'] = df['Agency Award Date (Most Recent)'].apply(
        lambda x: 'Accredited' if pd.notna(x) else 'Self-Assessment'
    )

    # Color mapping for program types
    color_map = {
        'Law Enforcement Accreditation': '#1f77b4',
        'Communications Accreditation': '#ff7f0e', 
        'Training Academy Accreditation': '#2ca02c'
    }
else:
    color_map = {}

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "CALEA Agencies Dashboard"

# Add custom CSS for fonts
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        {%css%}
        <style>
            body {
                font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
                font-weight: 400;
                line-height: 1.6;
            }
            
            h1, h2, h3, h4, h5, h6 {
                font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
                font-weight: 600;
                letter-spacing: -0.025em;
            }
            
            .dash-table-container {
                font-family: 'Inter', sans-serif;
            }
            
            .dash-table-container .dash-spreadsheet-inner * {
                font-family: 'Inter', sans-serif;
            }
            
            .dash-table-container .dash-header {
                font-family: 'Fira Code', monospace;
                font-weight: 600;
                background-color: #f8f9fa !important;
            }
            
            .stats-card {
                font-family: 'Inter', sans-serif;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: transform 0.2s ease;
            }
            
            .stats-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 16px rgba(0,0,0,0.15);
            }
            
            .stats-number {
                font-family: 'Fira Code', monospace;
                font-weight: 700;
                font-size: 2.2rem;
            }
            
            .filter-label {
                font-family: 'Fira Code', monospace;
                font-weight: 500;
                color: #2c3e50;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Define the layout
app.layout = html.Div([
    html.Div([
        html.H1("CALEA Agencies Interactive Dashboard", 
                style={'textAlign': 'center', 'marginBottom': 30, 'color': '#2c3e50'}),
        
        html.Div([
            html.Div([
                html.Label("Program Type:", className='filter-label', style={'marginBottom': 10, 'display': 'block'}),
                dcc.Dropdown(
                    id='program-type-filter',
                    options=[{'label': 'All', 'value': 'all'}] + 
                           [{'label': ptype, 'value': ptype} for ptype in df['Program Type'].dropna().unique()],
                    value='all',
                    style={'marginBottom': 20}
                )
            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '3%'}),
            
            html.Div([
                html.Label("Agency Size:", className='filter-label', style={'marginBottom': 10, 'display': 'block'}),
                dcc.Dropdown(
                    id='size-filter',
                    options=[{'label': 'All', 'value': 'all'}] + 
                           [{'label': size, 'value': size} for size in df['Size Category'].unique()],
                    value='all',
                    style={'marginBottom': 20}
                )
            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '3%'}),
            
            html.Div([
                html.Label("Award Status:", className='filter-label', style={'marginBottom': 10, 'display': 'block'}),
                dcc.Dropdown(
                    id='award-filter',
                    options=[{'label': 'All', 'value': 'all'}] + 
                           [{'label': status, 'value': status} for status in df['Award Status'].unique()],
                    value='all',
                    style={'marginBottom': 20}
                )
            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ], style={'marginBottom': 30}),
        
        # Summary statistics
        html.Div(id='summary-stats', style={'marginBottom': 30}),
        
        # Map with interaction instructions and quick zoom buttons
        html.Div([
            html.Div([
                html.P("💡 Map Interactions: Scroll to zoom • Click and drag to pan • Double-click to reset view • Hover markers for details", 
                       style={'fontSize': '13px', 'color': '#7f8c8d', 'fontFamily': 'Inter, sans-serif', 'margin': '0', 'textAlign': 'center'}),
            ], style={'marginBottom': '10px'}),
            
            html.Div([
                html.Span("Quick Zoom: ", style={'fontSize': '12px', 'color': '#2c3e50', 'fontFamily': 'Fira Code, monospace', 'marginRight': '10px'}),
                html.Button("🇺🇸 USA", id='zoom-usa', n_clicks=0, 
                           style={'fontSize': '11px', 'padding': '4px 8px', 'margin': '0 2px', 'border': '1px solid #bdc3c7', 'borderRadius': '4px', 'backgroundColor': '#ecf0f1', 'cursor': 'pointer'}),
                html.Button("🌊 West", id='zoom-west', n_clicks=0,
                           style={'fontSize': '11px', 'padding': '4px 8px', 'margin': '0 2px', 'border': '1px solid #bdc3c7', 'borderRadius': '4px', 'backgroundColor': '#ecf0f1', 'cursor': 'pointer'}),
                html.Button("🌾 Central", id='zoom-central', n_clicks=0,
                           style={'fontSize': '11px', 'padding': '4px 8px', 'margin': '0 2px', 'border': '1px solid #bdc3c7', 'borderRadius': '4px', 'backgroundColor': '#ecf0f1', 'cursor': 'pointer'}),
                html.Button("🏙️ East", id='zoom-east', n_clicks=0,
                           style={'fontSize': '11px', 'padding': '4px 8px', 'margin': '0 2px', 'border': '1px solid #bdc3c7', 'borderRadius': '4px', 'backgroundColor': '#ecf0f1', 'cursor': 'pointer'}),
                html.Button("☀️ South", id='zoom-south', n_clicks=0,
                           style={'fontSize': '11px', 'padding': '4px 8px', 'margin': '0 2px', 'border': '1px solid #bdc3c7', 'borderRadius': '4px', 'backgroundColor': '#ecf0f1', 'cursor': 'pointer'})
            ], style={'textAlign': 'center', 'marginBottom': '15px'}),
            
            dcc.Graph(
                id='agencies-map', 
                style={'height': '600px'},
                config={
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToAdd': ['pan2d', 'select2d', 'lasso2d'],
                    'modeBarButtonsToRemove': ['autoScale2d'],
                    'scrollZoom': True,
                    'doubleClick': 'reset+autosize',
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': 'calea_agencies_map',
                        'height': 600,
                        'width': 1200,
                        'scale': 2
                    }
                }
            )
        ]),
        
        # Data table
        html.H3("Agency Details", style={'marginTop': 30, 'marginBottom': 20}),
        dash_table.DataTable(
            id='agencies-table',
            columns=[
                {'name': 'Agency Name', 'id': 'Parent Organization Info Name', 'type': 'text'},
                {'name': 'City', 'id': 'Parent Organization Info Primary Address City', 'type': 'text'},
                {'name': 'State', 'id': 'Parent Organization Info Primary Address State Code', 'type': 'text'},
                {'name': 'Program Type', 'id': 'Program Type', 'type': 'text'},
                {'name': 'Award Status', 'id': 'Award Status', 'type': 'text'},
                {'name': 'CEO Name', 'id': 'CEO Full Name', 'type': 'text'},
                {'name': 'CEO Title', 'id': 'CEO Title', 'type': 'text'}
            ],
            data=[],
            filter_action='native',
            sort_action='native',
            sort_mode='multi',
            page_action='native',
            page_current=0,
            page_size=20,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '12px',
                'fontFamily': 'Inter, sans-serif',
                'fontSize': '14px',
                'border': '1px solid #e9ecef'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': '600',
                'fontFamily': 'Fira Code, monospace',
                'fontSize': '13px',
                'color': '#2c3e50',
                'border': '1px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ],
            tooltip_data=[],
            tooltip_duration=None,
            css=[{
                'selector': '.dash-table-tooltip',
                'rule': 'background-color: #2c3e50; color: white; font-family: Inter, sans-serif;'
            }]
        )
        
    ], style={'margin': '20px'})
])

@callback(
    [Output('agencies-map', 'figure'),
     Output('summary-stats', 'children'),
     Output('agencies-table', 'data')],
    [Input('program-type-filter', 'value'),
     Input('size-filter', 'value'),
     Input('award-filter', 'value'),
     Input('zoom-usa', 'n_clicks'),
     Input('zoom-west', 'n_clicks'),
     Input('zoom-central', 'n_clicks'),
     Input('zoom-east', 'n_clicks'),
     Input('zoom-south', 'n_clicks')]
)
def update_dashboard(program_type, size_category, award_status, zoom_usa, zoom_west, zoom_central, zoom_east, zoom_south):
    # Determine which zoom button was clicked (if any)
    ctx = dash.callback_context
    zoom_center = {"lat": 39.5, "lon": -98.35}  # Default USA center
    zoom_level = 3.5  # Default zoom
    
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'zoom-usa':
            zoom_center, zoom_level = {"lat": 39.5, "lon": -98.35}, 3.5
        elif button_id == 'zoom-west':
            zoom_center, zoom_level = {"lat": 39.0, "lon": -120.0}, 4.5  # West Coast
        elif button_id == 'zoom-central':
            zoom_center, zoom_level = {"lat": 39.0, "lon": -95.0}, 4.5   # Central US
        elif button_id == 'zoom-east':
            zoom_center, zoom_level = {"lat": 39.0, "lon": -77.0}, 4.5   # East Coast
        elif button_id == 'zoom-south':
            zoom_center, zoom_level = {"lat": 31.0, "lon": -95.0}, 4.5   # Southern States
    
    # Filter the data
    filtered_df = df.copy()
    
    if program_type != 'all':
        filtered_df = filtered_df[filtered_df['Program Type'] == program_type]
    
    if size_category != 'all':
        filtered_df = filtered_df[filtered_df['Size Category'] == size_category]
    
    if award_status != 'all':
        filtered_df = filtered_df[filtered_df['Award Status'] == award_status]
    
    # Create the map
    if len(filtered_df) > 0:
        # Create hover text
        filtered_df['hover_text'] = (
            '<b>' + filtered_df['Parent Organization Info Name'].astype(str) + '</b><br>' +
            filtered_df['Parent Organization Info Primary Address City'].astype(str) + ', ' + 
            filtered_df['Parent Organization Info Primary Address State Code'].astype(str) + '<br>' +
            'Program Type: ' + filtered_df['Program Type'].fillna('Unknown').astype(str) + '<br>' +
            'Sworn Personnel: ' + filtered_df['Extension Program Authorized Full Time Sworn Personnel'].astype(str) + '<br>' +
            'Award Status: ' + filtered_df['Award Status'].astype(str)
        )
        
        # Create a simple scatter mapbox plot with uniform marker size
        fig = px.scatter_mapbox(
            filtered_df,
            lat="Latitude",
            lon="Longitude",
            color="Program Type",
            color_discrete_map=color_map,
            hover_name="Parent Organization Info Name",
            hover_data={
                'Parent Organization Info Primary Address City': True,
                'Parent Organization Info Primary Address State Code': True,
                'Program Type': True,
                'Award Status': True,
                'Latitude': False,
                'Longitude': False
            },
            mapbox_style="carto-positron",
            zoom=zoom_level,
            center=zoom_center,
            height=600,
            title="CALEA Agencies Distribution"
        )
        
        # Set uniform marker size
        fig.update_traces(marker=dict(size=8))
        
        fig.update_layout(
            mapbox_style="carto-positron",
            margin={"r":0,"t":50,"l":0,"b":0},
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.8)"
            ),
            # Enhanced map interactions
            dragmode="pan",
            uirevision="constant"
        )
        
        # Update map configuration for better interactions
        fig.update_mapboxes(
            accesstoken=None,  # Using free tiles
            style="carto-positron",
            center=zoom_center,
            zoom=zoom_level
        )
    else:
        fig = go.Figure()
        fig.add_annotation(
            text="No agencies match the selected filters",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(height=600)
    
    # Summary statistics
    total_agencies = len(filtered_df)
    accredited = len(filtered_df[filtered_df['Award Status'] == 'Accredited'])
    
    stats = html.Div([
        html.Div([
            html.H4(f"{total_agencies:,}", className='stats-number', style={'margin': 0, 'color': '#3498db'}),
            html.P("Total Agencies", style={'margin': 0, 'fontFamily': 'Inter, sans-serif', 'fontSize': '14px', 'color': '#7f8c8d'})
        ], className='stats-card', style={'textAlign': 'center', 'padding': '24px', 'backgroundColor': '#ffffff', 'flex': '1', 'margin': '0 10px', 'minHeight': '120px', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center'}),
        
        html.Div([
            html.H4(f"{accredited:,}", className='stats-number', style={'margin': 0, 'color': '#27ae60'}),
            html.P("Accredited", style={'margin': 0, 'fontFamily': 'Inter, sans-serif', 'fontSize': '14px', 'color': '#7f8c8d'})
        ], className='stats-card', style={'textAlign': 'center', 'padding': '24px', 'backgroundColor': '#ffffff', 'flex': '1', 'margin': '0 10px', 'minHeight': '120px', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center'}),
        
        html.Div([
            html.H4(f"{total_agencies - accredited:,}", className='stats-number', style={'margin': 0, 'color': '#e74c3c'}),
            html.P("Self-Assessment", style={'margin': 0, 'fontFamily': 'Inter, sans-serif', 'fontSize': '14px', 'color': '#7f8c8d'})
        ], className='stats-card', style={'textAlign': 'center', 'padding': '24px', 'backgroundColor': '#ffffff', 'flex': '1', 'margin': '0 10px', 'minHeight': '120px', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center'})
    ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'stretch', 'gap': '0px', 'margin': '0 20px'})
    
    # Prepare data for DataTable
    if len(filtered_df) > 0:
        table_data = filtered_df[[
            'Parent Organization Info Name',
            'Parent Organization Info Primary Address City',
            'Parent Organization Info Primary Address State Code',
            'Program Type',
            'Award Status',
            'CEO Full Name',
            'CEO Title'
        ]].fillna('')  # Replace NaN values with empty strings
        
        # Convert to dictionary format for DataTable
        table_dict = table_data.to_dict('records')
    else:
        table_dict = []
    
    return fig, stats, table_dict

if __name__ == '__main__':
    app.run(debug=True, port=8050)