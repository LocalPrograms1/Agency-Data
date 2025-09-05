import dash
from dash import dcc, html, Input, Output, callback, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import os

# Load data
if os.path.exists("geocoded_results.csv"):
    df = pd.read_csv("geocoded_results.csv")
elif os.path.exists("NPI active client list 4.2.25.csv"):
    df = pd.read_csv("NPI active client list 4.2.25.csv")
else:
    raise FileNotFoundError("No data file found")

# Data preprocessing
df = df.dropna(subset=["Latitude", "Longitude"]).copy()
df["Personnel"] = pd.to_numeric(df["Extension Program Authorized Full Time Sworn Personnel"], errors="coerce").fillna(0)

def size_bin(p):
    if p < 25:
        return "Small (<25)"
    elif p < 100:
        return "Medium (25-99)"
    else:
        return "Large (100+)"

df["Size Group"] = df["Personnel"].apply(size_bin)

# Process award dates
def process_award_date(date_str):
    if pd.isna(date_str):
        return "Self-Assessment"
    try:
        return pd.to_datetime(date_str).strftime("%Y-%m-%d")
    except:
        return str(date_str)

df["Award Status"] = df.get("Agency Award Date", pd.Series([None] * len(df))).apply(
    lambda x: "Accredited" if not pd.isna(x) else "Self-Assessment"
)

# Color mappings
program_colors = {
    "Law Enforcement Accreditation": "#1f77b4",
    "Communications Accreditation": "#2ca02c", 
    "Training Academy Accreditation": "#d62728"
}

size_colors = {
    "Small (<25)": "#74c476",
    "Medium (25-99)": "#31a354", 
    "Large (100+)": "#006d2c"
}

# Initialize Dash app
app = dash.Dash(__name__)

# Custom CSS styles - only FontAwesome for icons
external_stylesheets = [
    'https://use.fontawesome.com/releases/v5.8.1/css/all.css'
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Add comprehensive custom CSS to override all fonts
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            * {
                font-family: Arial, Helvetica, sans-serif !important;
            }
            body, html {
                font-family: Arial, Helvetica, sans-serif !important;
            }
            h1, h2, h3, h4, h5, h6 {
                font-family: Arial, Helvetica, sans-serif !important;
            }
            p, span, div, label {
                font-family: Arial, Helvetica, sans-serif !important;
            }
            .dash-table-container, .dash-table-container * {
                font-family: Arial, Helvetica, sans-serif !important;
            }
            .Select-control, .Select-menu-outer, .Select-option {
                font-family: Arial, Helvetica, sans-serif !important;
            }
            .dash-dropdown, .dash-dropdown * {
                font-family: Arial, Helvetica, sans-serif !important;
            }
            .plotly .gtitle, .plotly .xtitle, .plotly .ytitle {
                font-family: Arial, Helvetica, sans-serif !important;
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

app.layout = html.Div([
    # Header
    html.Div([
        html.H1("CALEA Agency Dashboard", 
                className="header-title",
                style={
                    'textAlign': 'center',
                    'color': '#2c3e50',
                    'marginBottom': '30px',
                    'fontFamily': 'Arial, Helvetica, sans-serif',
                    'fontSize': '28px',
                    'fontWeight': '600'
                })
    ], style={'backgroundColor': '#ffffff', 'padding': '20px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
    
    # Main content
    html.Div([
        # KPI Cards Row
        html.Div([
            # Total Agencies Card
            html.Div([
                html.Div([
                    html.I(className="fas fa-building", style={'fontSize': '24px', 'color': '#3498db'}),
                    html.H3(id="total-agencies", children=str(len(df)), 
                           style={'margin': '10px 0 5px 0', 'color': '#2c3e50', 'fontFamily': 'Arial, Helvetica, sans-serif'}),
                    html.P("Total Agencies", style={'margin': '0', 'color': '#7f8c8d', 'fontSize': '14px', 'fontFamily': 'Arial, Helvetica, sans-serif'})
                ], style={'textAlign': 'center'})
            ], className="kpi-card", style={
                'backgroundColor': '#ffffff',
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                'margin': '10px'
            }),
            
            # Accredited Agencies Card  
            html.Div([
                html.Div([
                    html.I(className="fas fa-certificate", style={'fontSize': '24px', 'color': '#2ecc71'}),
                    html.H3(id="accredited-agencies", 
                           children=str(len(df[df["Award Status"] == "Accredited"])),
                           style={'margin': '10px 0 5px 0', 'color': '#2c3e50', 'fontFamily': 'Arial, Helvetica, sans-serif'}),
                    html.P("Accredited", style={'margin': '0', 'color': '#7f8c8d', 'fontSize': '14px', 'fontFamily': 'Arial, Helvetica, sans-serif'})
                ], style={'textAlign': 'center'})
            ], className="kpi-card", style={
                'backgroundColor': '#ffffff',
                'padding': '20px', 
                'borderRadius': '8px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                'margin': '10px'
            }),
            
            # Self-Assessment Card
            html.Div([
                html.Div([
                    html.I(className="fas fa-clipboard-check", style={'fontSize': '24px', 'color': '#f39c12'}),
                    html.H3(id="self-assessment", 
                           children=str(len(df[df["Award Status"] == "Self-Assessment"])),
                           style={'margin': '10px 0 5px 0', 'color': '#2c3e50', 'fontFamily': 'Arial, Helvetica, sans-serif'}),
                    html.P("Self-Assessment", style={'margin': '0', 'color': '#7f8c8d', 'fontSize': '14px', 'fontFamily': 'Arial, Helvetica, sans-serif'})
                ], style={'textAlign': 'center'})
            ], className="kpi-card", style={
                'backgroundColor': '#ffffff',
                'padding': '20px',
                'borderRadius': '8px', 
                'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                'margin': '10px'
            }),
            
            # Average Personnel Card
            html.Div([
                html.Div([
                    html.I(className="fas fa-users", style={'fontSize': '24px', 'color': '#9b59b6'}),
                    html.H3(id="avg-personnel", 
                           children=str(int(df["Personnel"].mean())),
                           style={'margin': '10px 0 5px 0', 'color': '#2c3e50', 'fontFamily': 'Arial, Helvetica, sans-serif'}),
                    html.P("Avg Personnel", style={'margin': '0', 'color': '#7f8c8d', 'fontSize': '14px', 'fontFamily': 'Arial, Helvetica, sans-serif'})
                ], style={'textAlign': 'center'})
            ], className="kpi-card", style={
                'backgroundColor': '#ffffff', 
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                'margin': '10px'
            })
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around', 'margin': '20px 0'}),
        
        # Filters Row
        html.Div([
            html.Div([
                html.Label("Program Type", style={'fontWeight': '600', 'color': '#2c3e50', 'marginBottom': '5px', 'fontFamily': 'Arial, Helvetica, sans-serif'}),
                dcc.Dropdown(
                    id='program-filter',
                    options=[{'label': 'All', 'value': 'All'}] + 
                           [{'label': pt, 'value': pt} for pt in df['Program Type'].dropna().unique()],
                    value='All',
                    style={'marginBottom': '15px'}
                )
            ], style={'width': '30%', 'display': 'inline-block', 'margin': '0 1.5%'}),
            
            html.Div([
                html.Label("Size Group", style={'fontWeight': '600', 'color': '#2c3e50', 'marginBottom': '5px', 'fontFamily': 'Arial, Helvetica, sans-serif'}),
                dcc.Dropdown(
                    id='size-filter',
                    options=[{'label': 'All', 'value': 'All'}] + 
                           [{'label': sg, 'value': sg} for sg in df['Size Group'].unique()],
                    value='All',
                    style={'marginBottom': '15px'}
                )
            ], style={'width': '30%', 'display': 'inline-block', 'margin': '0 1.5%'}),
            
            html.Div([
                html.Label("Award Status", style={'fontWeight': '600', 'color': '#2c3e50', 'marginBottom': '5px', 'fontFamily': 'Arial, Helvetica, sans-serif'}),
                dcc.Dropdown(
                    id='award-filter',
                    options=[
                        {'label': 'All', 'value': 'All'},
                        {'label': 'Accredited', 'value': 'Accredited'},
                        {'label': 'Self-Assessment', 'value': 'Self-Assessment'}
                    ],
                    value='All',
                    style={'marginBottom': '15px'}
                )
            ], style={'width': '30%', 'display': 'inline-block', 'margin': '0 1.5%'})
        ], style={'backgroundColor': '#ffffff', 'padding': '20px', 'borderRadius': '8px', 
                 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)', 'margin': '20px'}),
        
        # Charts Row
        html.Div([
            # Map
            html.Div([
                html.H3("Geographic Distribution", 
                       style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '20px', 'fontFamily': 'Arial, Helvetica, sans-serif'}),
                dcc.Graph(id='agency-map')
            ], style={'width': '65%', 'display': 'inline-block', 'backgroundColor': '#ffffff',
                     'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                     'margin': '10px'}),
            
            # Program Type Distribution
            html.Div([
                html.H3("Program Distribution", 
                       style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '20px', 'fontFamily': 'Arial, Helvetica, sans-serif'}),
                dcc.Graph(id='program-chart')
            ], style={'width': '30%', 'display': 'inline-block', 'backgroundColor': '#ffffff',
                     'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                     'margin': '10px'})
        ]),
        
        # Size and Personnel Charts
        html.Div([
            html.Div([
                html.H3("Agency Size Distribution", 
                       style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '20px', 'fontFamily': 'Arial, Helvetica, sans-serif'}),
                dcc.Graph(id='size-chart')
            ], style={'width': '48%', 'display': 'inline-block', 'backgroundColor': '#ffffff',
                     'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                     'margin': '1%'}),
            
            html.Div([
                html.H3("Personnel vs Program Type", 
                       style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '20px', 'fontFamily': 'Arial, Helvetica, sans-serif'}),
                dcc.Graph(id='personnel-scatter')
            ], style={'width': '48%', 'display': 'inline-block', 'backgroundColor': '#ffffff',
                     'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                     'margin': '1%'})
        ], style={'margin': '20px 0'}),
        
        # Data Table
        html.Div([
            html.H3("Agency Details", 
                   style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '20px', 'fontFamily': 'Arial, Helvetica, sans-serif'}),
            dash_table.DataTable(
                id='agency-table',
                columns=[
                    {'name': 'Agency Name', 'id': 'Parent Organization Info Name'},
                    {'name': 'City', 'id': 'Parent Organization Info Primary Address City'},
                    {'name': 'State', 'id': 'Parent Organization Info Primary Address State Code'},
                    {'name': 'Program Type', 'id': 'Program Type'},
                    {'name': 'Personnel', 'id': 'Personnel', 'type': 'numeric'},
                    {'name': 'Size Group', 'id': 'Size Group'},
                    {'name': 'Award Status', 'id': 'Award Status'}
                ],
                data=df.to_dict('records'),
                filter_action='native',
                sort_action='native',
                page_size=10,
                style_cell={'textAlign': 'left', 'padding': '10px', 'fontFamily': 'Arial, Helvetica, sans-serif'},
                style_header={'backgroundColor': '#3498db', 'color': 'white', 'fontWeight': '600', 'fontFamily': 'Arial, Helvetica, sans-serif'},
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{Award Status} = Accredited'},
                        'backgroundColor': '#d5f4e6',
                    },
                    {
                        'if': {'filter_query': '{Award Status} = Self-Assessment'},
                        'backgroundColor': '#fff3cd',
                    }
                ]
            )
        ], style={'backgroundColor': '#ffffff', 'padding': '20px', 'borderRadius': '8px',
                 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)', 'margin': '20px'})
        
    ], style={'backgroundColor': '#f8f9fa', 'minHeight': '100vh', 'padding': '0'})
])

# Callbacks
@app.callback(
    [Output('agency-map', 'figure'),
     Output('program-chart', 'figure'), 
     Output('size-chart', 'figure'),
     Output('personnel-scatter', 'figure'),
     Output('agency-table', 'data'),
     Output('total-agencies', 'children'),
     Output('accredited-agencies', 'children'),
     Output('self-assessment', 'children'),
     Output('avg-personnel', 'children')],
    [Input('program-filter', 'value'),
     Input('size-filter', 'value'),
     Input('award-filter', 'value')]
)
def update_dashboard(program_filter, size_filter, award_filter):
    # Filter data
    filtered_df = df.copy()
    
    if program_filter != 'All':
        filtered_df = filtered_df[filtered_df['Program Type'] == program_filter]
    if size_filter != 'All':
        filtered_df = filtered_df[filtered_df['Size Group'] == size_filter]  
    if award_filter != 'All':
        filtered_df = filtered_df[filtered_df['Award Status'] == award_filter]
    
    # Map
    map_fig = px.scatter_mapbox(
        filtered_df,
        lat='Latitude',
        lon='Longitude', 
        color='Program Type',
        size='Personnel',
        hover_name='Parent Organization Info Name',
        hover_data=['Parent Organization Info Primary Address City', 
                   'Parent Organization Info Primary Address State Code',
                   'Award Status'],
        color_discrete_map=program_colors,
        size_max=20,
        zoom=3,
        center={'lat': 39.5, 'lon': -98.35},
        mapbox_style='carto-positron',
        height=500
    )
    map_fig.update_layout(margin={'r':0,'t':0,'l':0,'b':0}, font_family='Arial, Helvetica, sans-serif')
    
    # Program type chart
    program_counts = filtered_df['Program Type'].value_counts()
    program_fig = px.pie(
        values=program_counts.values,
        names=program_counts.index,
        color=program_counts.index,
        color_discrete_map=program_colors,
        height=400
    )
    program_fig.update_traces(textposition='inside', textinfo='percent+label')
    program_fig.update_layout(showlegend=False, margin={'r':0,'t':0,'l':0,'b':0}, font_family='Arial, Helvetica, sans-serif')
    
    # Size chart  
    size_counts = filtered_df['Size Group'].value_counts()
    size_fig = px.bar(
        x=size_counts.index,
        y=size_counts.values,
        color=size_counts.index,
        color_discrete_map=size_colors,
        height=400
    )
    size_fig.update_layout(showlegend=False, xaxis_title="Size Group", yaxis_title="Count",
                          margin={'r':0,'t':0,'l':0,'b':0}, font_family='Arial, Helvetica, sans-serif')
    
    # Personnel scatter
    personnel_fig = px.box(
        filtered_df,
        x='Program Type',
        y='Personnel', 
        color='Program Type',
        color_discrete_map=program_colors,
        height=400
    )
    personnel_fig.update_layout(showlegend=False, margin={'r':0,'t':0,'l':0,'b':0}, font_family='Arial, Helvetica, sans-serif')
    
    # Update KPIs
    total_agencies = str(len(filtered_df))
    accredited = str(len(filtered_df[filtered_df['Award Status'] == 'Accredited']))
    self_assessment = str(len(filtered_df[filtered_df['Award Status'] == 'Self-Assessment']))
    avg_personnel = str(int(filtered_df['Personnel'].mean())) if len(filtered_df) > 0 else "0"
    
    return (map_fig, program_fig, size_fig, personnel_fig, filtered_df.to_dict('records'),
            total_agencies, accredited, self_assessment, avg_personnel)

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)