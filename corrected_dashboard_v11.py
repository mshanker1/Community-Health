import dash
from dash import dcc, html, Input, Output, callback, State
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import numpy as np
import math
from datetime import datetime

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "County Health Dashboard - V11"

# Database connection functions
def get_database_connection():
    """Get connection to county health database"""
    return sqlite3.connect('county_health.db')

def get_all_counties():
    """Get list of all counties for dropdown"""
    conn = get_database_connection()
    
    # First, check what tables exist
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Available tables:", tables)
    
    # Try different possible table structures
    counties_df = pd.DataFrame()
    
    try:
        # First try the counties table
        counties_df = pd.read_sql("""
            SELECT fips_code, county_name, state_code, state_name
            FROM counties 
            ORDER BY state_code, county_name
        """, conn)
        print(f"Found {len(counties_df)} counties in 'counties' table")
    except Exception as e1:
        print(f"Could not read from 'counties' table: {e1}")
        try:
            # Try the county_data table
            counties_df = pd.read_sql("""
                SELECT FIPS as fips_code, County as county_name, State as state_code
                FROM county_data 
                ORDER BY State, County
            """, conn)
            print(f"Found {len(counties_df)} counties in 'county_data' table")
        except Exception as e2:
            print(f"Could not read from 'county_data' table: {e2}")
            # Return empty dataframe if both fail
            counties_df = pd.DataFrame(columns=['fips_code', 'county_name', 'state_code'])
    
    # Clean up any null values
    if not counties_df.empty:
        counties_df = counties_df.dropna(subset=['fips_code', 'county_name', 'state_code'])
        print(f"After cleaning: {len(counties_df)} counties")
    
    conn.close()
    return counties_df

def get_county_metrics(county_fips):
    """Get all metrics for a specific county"""
    conn = get_database_connection()
    
    # Get the full row for this county
    county_data = pd.read_sql("""
        SELECT * FROM county_data 
        WHERE FIPS = ?
    """, conn, params=[county_fips])
    
    conn.close()
    
    if county_data.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Extract county info
    county_info = pd.DataFrame({
        'county_name': [county_data['County'].iloc[0]],
        'state_code': [county_data['State'].iloc[0]],
        'state_name': [county_data['State'].iloc[0]]
    })
    
    # Structure the metrics data
    metrics_data = structure_metrics_from_columns(county_data)
    
    return county_info, metrics_data

def structure_metrics_from_columns(county_data):
    """Structure metrics data from column-based format"""
    if county_data.empty:
        return {}
    
    structured = {
        'society': {},
        'economy': {},
        'nature': {}
    }
    
    # Get all columns except the first three (FIPS, State, County)
    metric_columns = county_data.columns[3:]
    
    for col in metric_columns:
        parts = col.split('_')
        if len(parts) >= 2:
            top_level = parts[0].lower()
            sub_category = parts[1].upper()
            
            if top_level in structured:
                # Get the value
                value = county_data[col].iloc[0]
                if pd.notna(value) and value != '':
                    try:
                        numeric_value = float(value)
                        # Store the sub-category if not already there
                        if sub_category not in structured[top_level]:
                            structured[top_level][sub_category] = numeric_value
                    except:
                        pass
    
    return structured

def create_sector_based_radar_chart(county_data, county_name):
    """Create radar chart with proper sector distribution"""
    if not county_data:
        return go.Figure()
    
    # Define categories with colors and sector assignments
    categories_config = {
        'society': {'color': '#2563EB', 'label': 'SOCIETY', 'start_angle': 0, 'end_angle': 120},
        'economy': {'color': '#DC2626', 'label': 'ECONOMY', 'start_angle': 120, 'end_angle': 240}, 
        'nature': {'color': '#059669', 'label': 'NATURE', 'start_angle': 240, 'end_angle': 360}
    }
    
    fig = go.Figure()
    
    # Process each category separately
    all_theta = []
    all_r = []
    all_colors = []
    all_hover = []
    all_customdata = []
    all_labels = []
    
    for category in ['society', 'economy', 'nature']:
        if category in county_data and county_data[category]:
            config = categories_config[category]
            sub_categories = list(county_data[category].keys())
            values = list(county_data[category].values())
            
            # Calculate angles for this sector
            n_metrics = len(sub_categories)
            if n_metrics > 0:
                # Distribute metrics within the sector
                sector_span = config['end_angle'] - config['start_angle']
                # Leave some padding at sector boundaries
                padding = 5  # degrees
                effective_span = sector_span - 2 * padding
                
                if n_metrics == 1:
                    # Center single metric in sector
                    angles = [config['start_angle'] + sector_span / 2]
                else:
                    # Distribute multiple metrics evenly
                    step = effective_span / (n_metrics - 1)
                    angles = [config['start_angle'] + padding + i * step for i in range(n_metrics)]
                
                # Add to overall data
                for i, (sub_cat, value, angle) in enumerate(zip(sub_categories, values, angles)):
                    all_theta.append(angle)
                    all_r.append(value)
                    all_colors.append(config['color'])
                    all_hover.append(f"{config['label']}<br>{sub_cat}: {value:.1f}")
                    all_customdata.append([category, sub_cat])
                    all_labels.append(sub_cat)
    
    # Create the main radar trace
    fig.add_trace(go.Scatterpolar(
        r=all_r,
        theta=all_theta,
        fill='toself',
        fillcolor='rgba(100,100,100,0.1)',
        line=dict(color='rgba(100,100,100,0.6)', width=2),
        marker=dict(
            size=12,
            color=all_colors,
            line=dict(color='white', width=2)
        ),
        name='County Metrics',
        text=all_hover,
        hovertemplate='%{text}<extra></extra>',
        customdata=all_customdata,
        mode='markers+lines'
    ))
    
    # Add labels for each point
    for i, (theta, r, label, color) in enumerate(zip(all_theta, all_r, all_labels, all_colors)):
        # Convert angle to radians (Plotly uses degrees, but we need radians for calculations)
        angle_rad = math.radians(theta)
        
        # Position label slightly outside the point
        label_r = min(r + 10, 95)  # Keep labels inside the chart area
        
        # Calculate label position in polar coordinates
        label_x = label_r * math.sin(angle_rad)
        label_y = label_r * math.cos(angle_rad)
        
        # Add text trace instead of annotation for better visibility
        fig.add_trace(go.Scatterpolar(
            r=[label_r],
            theta=[theta],
            mode='text',
            text=[label],
            textfont=dict(
                size=11,
                color=color,
                family="Arial, sans-serif",
                weight=600
            ),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Add sector arcs and labels
    for category, config in categories_config.items():
        # Draw sector arc at the outermost circle (100)
        arc_angles = list(range(int(config['start_angle']), int(config['end_angle']) + 1, 2))
        arc_r = [100] * len(arc_angles)
        
        fig.add_trace(go.Scatterpolar(
            r=arc_r,
            theta=arc_angles,
            mode='lines',
            line=dict(color=config['color'], width=6),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Add sector boundaries (radial lines) - including the 0/360 degree line
        if category == 'society':
            # Add the 0 degree line for society
            fig.add_trace(go.Scatterpolar(
                r=[0, 105],
                theta=[0, 0],
                mode='lines',
                line=dict(color=config['color'], width=2, dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Add the end boundary line
        fig.add_trace(go.Scatterpolar(
            r=[0, 105],
            theta=[config['end_angle'], config['end_angle']],
            mode='lines',
            line=dict(color=config['color'], width=2, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Add category label on the circumference
        mid_angle = (config['start_angle'] + config['end_angle']) / 2
        
        # Add text trace for sector labels - now positioned outside the visible data area
        fig.add_trace(go.Scatterpolar(
            r=[114],  # Now safe to position at 110 since range extends to 120
            theta=[mid_angle],
            mode='text',
            text=[config['label']],
            textfont=dict(
                size=18,
                color=config['color'],
                family="Arial, sans-serif",
                weight=900
            ),
            textposition="middle center",
            showlegend=False,
            hoverinfo='skip'
        ))
    # Add concentric circles for reference
    for radius in [20, 40, 60, 80, 100]:
        circle_theta = list(range(0, 361, 5))
        circle_r = [radius] * len(circle_theta)
        
        fig.add_trace(go.Scatterpolar(
            r=circle_r,
            theta=circle_theta,
            mode='lines',
            line=dict(color='rgba(200,200,200,0.3)', width=1),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            bgcolor='white',
            radialaxis=dict(
                visible=True,
                range=[0, 120],  # Extended from 100 to 120 to accommodate labels
                tickfont=dict(size=12, color='#374151'),
                gridcolor='rgba(150,150,150,0.3)',
                tickmode='linear',
                tick0=0,
                dtick=20,
                tickvals=[0, 20, 40, 60, 80, 100],  # Specify tick values to stop at 100
                ticktext=['0', '20', '40', '60', '80', '100']  # Custom tick labels
            ),
            angularaxis=dict(
                tickmode='array',
                tickvals=[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330],
                ticktext=[''] * 12,  # Hide angular labels
                gridcolor='rgba(150,150,150,0.2)',
                showticklabels=False
            )
        ),
        showlegend=False,
        title=dict(
            text=f"<b>{county_name} Health Metrics Overview</b>",
            x=0.5,
            font=dict(size=22, color='#1F2937')
        ),
        height=700,
        margin=dict(t=100, b=100, l=100, r=100),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    return fig

def get_submetric_details(county_fips, top_level, sub_category):
    """Get detailed metrics for a specific sub-category"""
    conn = get_database_connection()
    
    # Get all columns that match the pattern
    county_data = pd.read_sql("""
        SELECT * FROM county_data 
        WHERE FIPS = ?
    """, conn, params=[county_fips])
    
    conn.close()
    
    if county_data.empty:
        return pd.DataFrame()
    
    # Find all columns that start with the pattern
    pattern = f"{top_level}_{sub_category}_"
    matching_columns = [col for col in county_data.columns if col.upper().startswith(pattern.upper())]
    
    # Create details dataframe
    details = []
    for col in matching_columns:
        parts = col.split('_', 2)
        if len(parts) >= 3:
            metric_name = parts[2]
            value = county_data[col].iloc[0]
            if pd.notna(value) and value != '':
                try:
                    numeric_value = float(value)
                    details.append({
                        'metric_name': metric_name.replace('KEYINDICATOR', '').title(),
                        'metric_value': numeric_value,
                        'percentile_rank': 50  # Placeholder - you'd calculate this from all counties
                    })
                except:
                    pass
    
    return pd.DataFrame(details)

def create_detail_chart(details_df, title):
    """Create detailed bar chart for sub-metrics"""
    if details_df.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=details_df['metric_name'],
        x=details_df['metric_value'],
        orientation='h',
        marker=dict(
            color=details_df['percentile_rank'],
            colorscale='RdYlGn',
            colorbar=dict(title="Percentile Rank"),
            cmin=0,
            cmax=100
        ),
        text=[f"{val:.1f}" for val in details_df['metric_value']],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>Value: %{x:.1f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18)),
        xaxis_title="Metric Value",
        yaxis_title="Metrics",
        height=max(400, len(details_df) * 50),
        margin=dict(l=200, r=50, t=50, b=50)
    )
    
    return fig

# Load initial data
counties_df = get_all_counties()

# Create county options for dropdown
county_options = []
default_value = None

if not counties_df.empty:
    county_options = [
        {'label': f"{row['county_name']}, {row['state_code']}", 'value': row['fips_code']}
        for _, row in counties_df.iterrows()
    ]
    default_value = counties_df.iloc[0]['fips_code']
else:
    # Provide a default empty option if no data
    county_options = [{'label': 'No counties found', 'value': 'none'}]
    default_value = 'none'

print(f"Created {len(county_options)} county options")
print(f"Default value: {default_value}")

# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("County Health Dashboard - V11", 
                className="text-3xl font-bold text-center text-gray-800 mb-6"),
        
        html.Div([
            html.Label("Select County:", className="font-medium mr-3"),
            dcc.Dropdown(
                id='county-selector',
                options=county_options,
                value=default_value,
                style={'width': '300px'},
                className="inline-block"
            )
        ], className="flex justify-center items-center mb-6")
    ], className="bg-white p-6 rounded-lg shadow-md mb-6"),
    
    # Main content
    html.Div([
        # Radar chart section
        html.Div([
            dcc.Graph(
                id='radar-chart',
                style={'height': '700px'}
            )
        ], className="bg-white p-6 rounded-lg shadow-md", style={'width': '65%'}),
        
        # Summary section
        html.Div([
            html.Div([
                html.H3("Quick Stats", className="text-lg font-semibold mb-4"),
                html.Div(id='summary-stats')
            ], className="bg-white p-4 rounded-lg shadow-md mb-4"),
            
            html.Div([
                html.H3("Actions", className="text-lg font-semibold mb-4"),
                html.Button("Compare with State", 
                           className="w-full mb-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"),
                html.Button("View Trends", 
                           className="w-full mb-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"),
                html.Button("Generate Report", 
                           className="w-full mb-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700")
            ], className="bg-white p-4 rounded-lg shadow-md mb-4"),
            
            html.Div([
                html.H3("Instructions", className="text-lg font-semibold mb-4"),
                html.Ul([
                    html.Li("Click on radar chart points to see detailed metrics"),
                    html.Li("Each sector represents a major category"),
                    html.Li("Society (Blue), Economy (Red), Nature (Green)"),
                    html.Li("Sub-measures are distributed within their sectors")
                ], className="text-sm text-gray-600 space-y-1 list-disc list-inside")
            ], className="bg-white p-4 rounded-lg shadow-md")
        ], style={'width': '33%', 'marginLeft': '2%'})
    ], className="flex"),
    
    # Detail section
    html.Div([
        html.H2(id='detail-title', className="text-xl font-semibold mb-4"),
        dcc.Graph(id='detail-chart')
    ], id='detail-section', className="bg-white p-6 rounded-lg shadow-md mt-6", 
       style={'display': 'none'}),
    
    # Data stores
    dcc.Store(id='county-data-store'),
    dcc.Store(id='selected-county-info')
    
], className="min-h-screen bg-gray-100 p-6 max-w-7xl mx-auto")

# Callbacks
@app.callback(
    [Output('county-data-store', 'data'),
     Output('selected-county-info', 'data')],
    Input('county-selector', 'value')
)
def update_county_data(selected_county):
    if not selected_county:
        return {}, {}
    
    county_info, structured_data = get_county_metrics(selected_county)
    
    if county_info.empty:
        return {}, {}
    
    county_details = {
        'county_name': county_info.iloc[0]['county_name'],
        'state_code': county_info.iloc[0]['state_code'],
        'state_name': county_info.iloc[0]['state_name'],
        'fips': selected_county
    }
    
    return structured_data, county_details

@app.callback(
    Output('radar-chart', 'figure'),
    [Input('county-data-store', 'data'),
     Input('selected-county-info', 'data')]
)
def update_radar_chart(county_data, county_info):
    if not county_data or not county_info:
        return go.Figure()
    
    county_name = f"{county_info['county_name']}, {county_info['state_code']}"
    return create_sector_based_radar_chart(county_data, county_name)

@app.callback(
    Output('summary-stats', 'children'),
    Input('county-data-store', 'data')
)
def update_summary_stats(county_data):
    if not county_data:
        return "No data available"
    
    category_colors = {
        'society': '#2563EB',
        'economy': '#DC2626', 
        'nature': '#059669'
    }
    
    stats_items = []
    for category in ['society', 'economy', 'nature']:
        if category in county_data and county_data[category]:
            subcats = county_data[category]
            avg_score = round(sum(subcats.values()) / len(subcats), 1)
            color = category_colors[category]
            
            stats_items.append(
                html.Div([
                    html.Div([
                        html.Span(category.upper(), className="font-medium text-white text-sm"),
                    ], className="px-3 py-1 rounded", style={'backgroundColor': color}),
                    html.Span(str(avg_score), className="text-xl font-bold", style={'color': color})
                ], className="flex justify-between items-center p-3 bg-gray-50 rounded mb-2")
            )
    
    return stats_items

@app.callback(
    [Output('detail-section', 'style'),
     Output('detail-title', 'children'),
     Output('detail-chart', 'figure')],
    [Input('radar-chart', 'clickData')],
    [State('selected-county-info', 'data')]
)
def handle_radar_click(clickData, county_info):
    if not clickData or not county_info:
        return {'display': 'none'}, "", go.Figure()
    
    try:
        point_data = clickData['points'][0]
        custom_data = point_data.get('customdata', [])
        
        if len(custom_data) >= 2:
            top_level = custom_data[0]
            sub_category = custom_data[1]
            
            details_df = get_submetric_details(county_info['fips'], top_level, sub_category)
            
            if not details_df.empty:
                title = f"{sub_category.title()} Metrics - {county_info['county_name']}, {county_info['state_code']}"
                detail_fig = create_detail_chart(details_df, title)
                
                return {'display': 'block'}, title, detail_fig
    
    except Exception as e:
        print(f"Error handling click: {e}")
    
    return {'display': 'none'}, "", go.Figure()

# Custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <script src="https://cdn.tailwindcss.com"></script>
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
