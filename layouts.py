"""
Layout components for the dashboard
"""
from dash import dcc, html
from data_loader import get_metric_categories

def create_app_layout(df):
    """Create the main app layout"""
    return html.Div([
        # Store components for managing drill-down state
        dcc.Store(id='drill-down-state', data={
            'level': 'overview', 
            'selected_state': None, 
            'selected_county': None, 
            'selected_category': None, 
            'selected_metric': None
        }),
        dcc.Store(id='navigation-history', data=[]),
        
        # Header with navigation breadcrumbs
        html.Div([
            html.H1("County Well-Being Hierarchical Dashboard", className="header-title"),
            html.P("Interactive drill-down: Counties → Categories → Sub-metrics", className="header-subtitle"),
            html.Div(id='breadcrumb-nav', className="breadcrumb")
        ], className="header"),
        
        # Control Panel
        html.Div([
            html.Div([
                html.Label("View Level:", className="control-label"),
                dcc.RadioItems(
                    id='view-level',
                    options=[
                        {'label': 'County Overview', 'value': 'overview'},
                        {'label': 'Category Detail', 'value': 'category'},
                        {'label': 'Metric Analysis', 'value': 'metric'}
                    ],
                    value='overview',
                    className="radio-items"
                )
            ], className="control-item"),
            
            html.Div([
                html.Label("Select State:", className="control-label"),
                dcc.Dropdown(
                    id='state-dropdown',
                    options=[{'label': state, 'value': state} for state in sorted(df['State'].unique())],
                    placeholder="Choose a state...",
                    className="dropdown"
                )
            ], className="control-item"),
            
            html.Div([
                html.Label("Select County:", className="control-label"),
                dcc.Dropdown(
                    id='county-dropdown',
                    placeholder="Choose a county...",
                    className="dropdown",
                    disabled=True
                )
            ], className="control-item"),
            
            html.Div([
                html.Label("Select Category:", className="control-label"),
                dcc.Dropdown(
                    id='category-dropdown',
                    options=[{'label': cat, 'value': cat} for cat in get_metric_categories()],
                    placeholder="Choose a category...",
                    className="dropdown",
                    disabled=True
                )
            ], className="control-item"),
            
            html.Div([
                html.Button("Reset View", id="reset-button", className="reset-btn"),
                html.Button("Back", id="back-button", className="nav-btn", disabled=True)
            ], className="control-item")
        ], className="control-panel"),
        
        # Dynamic content area based on drill-down level
        html.Div(id='dynamic-content', className="main-content")
    ])

def create_overview_layout(drill_state):
    """Create overview layout showing main categories for selected county"""
    selected_state = drill_state.get('selected_state')
    selected_county = drill_state.get('selected_county')
    
    if selected_county and selected_state:
        title = f"Category Overview: {selected_county}, {selected_state}"
        instruction = "Click on radar chart segments to drill into category details"
    else:
        title = "County and State Overview"
        instruction = "Select a state/county or click on charts to drill down"
    
    return html.Div([
        html.H2(title, className="section-title"),
        html.P(instruction, className="instruction-text"),
        
        html.Div([
            html.Div([
                dcc.Graph(id='main-chart')
            ], className="chart-container"),
            
            html.Div([
                dcc.Graph(id='overview-chart')
            ], className="chart-container")
        ], className="charts-row"),
        
        html.Div([
            dcc.Graph(id='top-counties-chart')
        ], className="chart-container"),
        
        html.Div(id='overview-stats')
    ])

def create_category_layout(drill_state):
    """Create category detail view with sub-metrics"""
    from chart_functions import create_category_comparison_chart
    from stats_functions import create_category_stats
    
    selected_category = drill_state.get('selected_category')
    selected_state = drill_state.get('selected_state')
    selected_county = drill_state.get('selected_county')
    
    if not selected_category or not selected_state or not selected_county:
        return html.Div("Please select a state, county, and category to view details.")
    
    return html.Div([
        html.H2(f"Category Details: {selected_category} for {selected_county}, {selected_state}", className="section-title"),
        html.P("Click on radar chart segments to analyze specific sub-metrics", className="instruction-text"),
        
        html.Div([
            html.Div([
                dcc.Graph(id='main-chart')
            ], className="chart-container"),
            
            html.Div([
                dcc.Graph(id='category-comparison-chart')
            ], className="chart-container")
        ], className="charts-row"),
        
        html.Div(id='category-stats')
    ])

def create_metric_layout(drill_state):
    """Create metric-specific analysis view"""
    # Immediate defensive check
    if not drill_state:
        print(f"DEBUG: create_metric_layout - No drill_state provided!")
        return html.Div("No state data available")
    
    selected_metric = drill_state.get('selected_metric')
    selected_category = drill_state.get('selected_category')
    selected_state = drill_state.get('selected_state')
    selected_county = drill_state.get('selected_county')
    
    print(f"DEBUG: create_metric_layout called")
    print(f"DEBUG: Full drill state received: {drill_state}")
    print(f"DEBUG: Extracted - Metric: '{selected_metric}', Category: '{selected_category}'")
    print(f"DEBUG: Extracted - State: '{selected_state}', County: '{selected_county}'")
    
    # Log the exact type and value of selected_metric
    print(f"DEBUG: selected_metric type: {type(selected_metric)}, value: {repr(selected_metric)}")
    
    # Check each required field individually for better debugging
    missing_fields = []
    if not selected_metric or selected_metric == 'None' or str(selected_metric).strip() == '':
        missing_fields.append("metric")
        print(f"DEBUG: Metric is missing or invalid: {repr(selected_metric)}")
    if not selected_category:
        missing_fields.append("category")
        print(f"DEBUG: Category is missing: {repr(selected_category)}")
    if not selected_state:
        missing_fields.append("state")
        print(f"DEBUG: State is missing: {repr(selected_state)}")
    if not selected_county:
        missing_fields.append("county")
        print(f"DEBUG: County is missing: {repr(selected_county)}")
    
    if missing_fields:
        error_msg = f"Missing required fields for metric analysis: {', '.join(missing_fields)}"
        print(f"DEBUG: ERROR - {error_msg}")
        
        # Show the complete debugging information
        return html.Div([
            html.H2("Metric Analysis - Missing Data", className="section-title"),
            html.P(f"Missing: {', '.join(missing_fields)}", className="instruction-text"),
            html.Div([
                html.H4("Debug Information:"),
                html.P(f"Full state: {drill_state}", style={"font-family": "monospace", "background": "#f0f0f0", "padding": "10px", "word-break": "break-all"}),
                html.P(f"Metric value: {repr(selected_metric)}", style={"font-family": "monospace"}),
                html.P(f"Metric type: {type(selected_metric)}", style={"font-family": "monospace"}),
            ]),
            html.P("If the metric shows as valid above, there may be a callback conflict. Try refreshing and navigating again.")
        ])
    
    print(f"DEBUG: All required fields present, creating metric layout")
    
    return html.Div([
        html.H2(f"Metric Analysis: {selected_metric} ({selected_category})", className="section-title"),
        html.P(f"Deep dive into {selected_metric} performance for {selected_county}, {selected_state}", className="instruction-text"),
        
        # BEHAVIOR ANALYSIS FIRST - Show insights before charts
        html.Div([
            html.H3("📊 Behavior Analysis", className="section-subtitle", style={"margin-top": "20px"}),
            html.Div(id='metric-insights')
        ], className="insights-section", style={"margin-bottom": "30px"}),
        
        # METRIC ANALYSIS SECOND - Show charts after insights
        html.Div([
            html.H3("📈 Metric Analysis", className="section-subtitle"),
            html.Div([
                html.Div([
                    dcc.Graph(id='metric-distribution-chart')
                ], className="chart-container"),
                html.Div([
                    dcc.Graph(id='peer-comparison-chart')
                ], className="chart-container")
            ], className="charts-row")
        ], className="charts-section")
    ])