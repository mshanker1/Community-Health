"""
Callback functions for the dashboard - FIXED VERSION
"""
import dash
from dash import Input, Output, State, html
from layouts import create_overview_layout, create_category_layout, create_metric_layout
from chart_functions import *
from stats_functions import *
from data_loader import get_category_sub_metrics, get_friendly_metric_name, create_display_to_column_mapping

def register_callbacks(app, df):
    """Register all callbacks for the dashboard"""
    
    # Main navigation callback
    @app.callback(
        [Output('drill-down-state', 'data'),
         Output('navigation-history', 'data'),
         Output('back-button', 'disabled')],
        [Input('reset-button', 'n_clicks'),
         Input('back-button', 'n_clicks')],
        [State('drill-down-state', 'data'),
         State('navigation-history', 'data')]
    )
    def manage_navigation(reset_clicks, back_clicks, current_state, nav_history):
        # Initialize navigation history if empty
        if not nav_history:
            nav_history = [{'level': 'overview', 'selected_state': None, 'selected_county': None, 
                           'selected_category': None, 'selected_metric': None}]
        
        # Determine which input triggered the callback
        ctx = dash.callback_context
        if not ctx.triggered:
            return current_state, nav_history, len(nav_history) <= 1
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Handle reset button
        if trigger_id == 'reset-button' and reset_clicks:
            new_state = {'level': 'overview', 'selected_state': None, 'selected_county': None, 
                        'selected_category': None, 'selected_metric': None}
            nav_history = [new_state]
            return new_state, nav_history, True
        
        # Handle back button
        if trigger_id == 'back-button' and back_clicks and len(nav_history) > 1:
            nav_history.pop()  # Remove current state
            new_state = nav_history[-1]  # Go to previous state
            return new_state, nav_history, len(nav_history) <= 1
        
        return current_state, nav_history, len(nav_history) <= 1

    # Sync controls with state - FIXED to prevent interference
    @app.callback(
        [Output('view-level', 'value'),
         Output('state-dropdown', 'value'),
         Output('county-dropdown', 'value'),
         Output('category-dropdown', 'value')],
        [Input('drill-down-state', 'data')],
        prevent_initial_call=True
    )
    def sync_controls_with_state(drill_state):
        print(f"DEBUG: sync_controls_with_state called with: {drill_state}")
        
        if not drill_state:
            print(f"DEBUG: No drill state, returning defaults")
            return 'overview', None, None, None
        
        result = (
            drill_state.get('level', 'overview'),
            drill_state.get('selected_state'),
            drill_state.get('selected_county'),
            drill_state.get('selected_category')
        )
        
        print(f"DEBUG: Syncing controls to: {result}")
        return result

    # Handle manual control changes - FIXED to preserve metric selection
    @app.callback(
        [Output('drill-down-state', 'data', allow_duplicate=True),
         Output('navigation-history', 'data', allow_duplicate=True)],
        [Input('view-level', 'value'),
         Input('state-dropdown', 'value'),
         Input('county-dropdown', 'value'),
         Input('category-dropdown', 'value')],
        [State('drill-down-state', 'data'),
         State('navigation-history', 'data')],
        prevent_initial_call=True
    )
    def handle_manual_changes(view_level, selected_state, selected_county, selected_category,
                             current_state, nav_history):
        if not nav_history:
            nav_history = []
        
        print(f"DEBUG: handle_manual_changes called")
        print(f"DEBUG: Inputs - level: {view_level}, state: {selected_state}, county: {selected_county}, category: {selected_category}")
        print(f"DEBUG: Current state: {current_state}")
        
        # Preserve the current metric if we're in metric level and just changing view controls
        current_metric = current_state.get('selected_metric') if current_state else None
        
        # Create new state based on manual selections
        new_state = {
            'level': view_level,
            'selected_state': selected_state,
            'selected_county': selected_county,
            'selected_category': selected_category,
            'selected_metric': current_metric if view_level == 'metric' else None  # Preserve metric for metric level
        }
        
        print(f"DEBUG: New state from manual changes: {new_state}")
        
        # Only add to history if it's significantly different from the last state
        if not nav_history or (
            nav_history[-1].get('level') != new_state['level'] or
            nav_history[-1].get('selected_state') != new_state['selected_state'] or
            nav_history[-1].get('selected_county') != new_state['selected_county'] or
            nav_history[-1].get('selected_category') != new_state['selected_category']
        ):
            nav_history.append(new_state)
            print(f"DEBUG: Added to navigation history")
        else:
            print(f"DEBUG: State not significantly different, not adding to history")
        
        return new_state, nav_history

    # Main chart click callback (always exists)
    @app.callback(
        [Output('drill-down-state', 'data', allow_duplicate=True),
         Output('navigation-history', 'data', allow_duplicate=True)],
        [Input('main-chart', 'clickData')],
        [State('drill-down-state', 'data'),
         State('navigation-history', 'data')],
        prevent_initial_call=True
    )
    def handle_main_chart_clicks(main_click, current_state, nav_history):
        if not nav_history:
            nav_history = []
        
        if not main_click or not current_state:
            return current_state, nav_history
        
        new_state = dict(current_state)  # Copy current state
        clicked_data = main_click['points'][0]
        current_level = current_state.get('level')
        
        print(f"DEBUG: Main chart clicked at level {current_level}")
        print(f"DEBUG: Clicked data: {clicked_data}")
        print(f"DEBUG: Current state before change: {current_state}")
        
        # If in overview and radar chart clicked, drill into category
        if current_level == 'overview' and 'theta' in clicked_data:
            clicked_category = clicked_data['theta']
            print(f"DEBUG: Category clicked: {clicked_category}")
            new_state['level'] = 'category'
            new_state['selected_category'] = clicked_category
            new_state['selected_metric'] = None
        
        # If in category view and sub-metric clicked, drill into metric analysis
        elif current_level == 'category' and 'theta' in clicked_data:
            clicked_metric_display = clicked_data['theta']
            category = current_state['selected_category']
            state = current_state['selected_state']
            county = current_state['selected_county']
            
            print(f"DEBUG: Sub-metric clicked: '{clicked_metric_display}'")
            print(f"DEBUG: Current category: {category}")
            print(f"DEBUG: Current state: {state}, county: {county}")
            
            if not category:
                print(f"DEBUG: ERROR - No category selected!")
                return current_state, nav_history
            
            # Get all sub-metrics for this category
            sub_metrics = get_category_sub_metrics(df, category)
            print(f"DEBUG: Available sub-metrics: {sub_metrics}")
            
            # Create a mapping from display names to column names
            display_to_column = {}
            column_to_display = {}
            
            for col in sub_metrics:
                friendly_name = get_friendly_metric_name(col)
                display_to_column[friendly_name] = col
                column_to_display[col] = friendly_name
                print(f"DEBUG: Mapping '{friendly_name}' <-> '{col}'")
            
            print(f"DEBUG: Looking for match for: '{clicked_metric_display}'")
            print(f"DEBUG: Available display names: {list(display_to_column.keys())}")
            
            # Find the matching column (try exact match first, then case-insensitive)
            matched_column = None
            if clicked_metric_display in display_to_column:
                matched_column = display_to_column[clicked_metric_display]
            else:
                # Try case-insensitive match
                for display_name, col_name in display_to_column.items():
                    if display_name.lower() == clicked_metric_display.lower():
                        matched_column = col_name
                        break
            
            if matched_column:
                # Extract just the metric part (everything after the first underscore)
                parts = matched_column.split('_')
                if len(parts) > 1:
                    metric_part = '_'.join(parts[1:])
                else:
                    metric_part = matched_column
                
                print(f"DEBUG: Matched column: {matched_column}")
                print(f"DEBUG: Extracted metric part: '{metric_part}'")
                
                # Update state
                new_state['level'] = 'metric'
                new_state['selected_metric'] = metric_part
                
                # Verify the full column name will exist
                full_metric_name = f"{category}_{metric_part}"
                print(f"DEBUG: Full metric name will be: '{full_metric_name}'")
                print(f"DEBUG: Column exists in df: {full_metric_name in df.columns}")
                
            else:
                print(f"DEBUG: ERROR - No match found for '{clicked_metric_display}'")
                print(f"DEBUG: This means the display name doesn't match any column")
                # Don't change state if no match found
                return current_state, nav_history
        
        # Add to history if state changed
        if new_state != current_state:
            nav_history.append(new_state)
            print(f"DEBUG: State changed successfully!")
            print(f"DEBUG: New state: {new_state}")
        else:
            print(f"DEBUG: State did not change")
        
        return new_state, nav_history

    # County dropdown update
    @app.callback(
        [Output('county-dropdown', 'options'),
         Output('county-dropdown', 'disabled')],
        [Input('state-dropdown', 'value')]
    )
    def update_county_dropdown(selected_state):
        if selected_state:
            counties = sorted(df[df['State'] == selected_state]['County'].unique())
            options = [{'label': county, 'value': county} for county in counties]
            return options, False
        return [], True

    # Category dropdown update
    @app.callback(
        Output('category-dropdown', 'disabled'),
        [Input('view-level', 'value')]
    )
    def update_category_dropdown(view_level):
        return view_level not in ['category', 'metric']

    # Breadcrumb navigation
    @app.callback(
        Output('breadcrumb-nav', 'children'),
        [Input('drill-down-state', 'data')]
    )
    def update_breadcrumbs(drill_state):
        breadcrumbs = []
        
        # Home
        breadcrumbs.append(html.Span("Home", className="breadcrumb-item"))
        
        # State level
        if drill_state and drill_state.get('selected_state'):
            breadcrumbs.append(html.Span(" > ", className="breadcrumb-separator"))
            breadcrumbs.append(html.Span(drill_state['selected_state'], className="breadcrumb-item"))
        
        # County level  
        if drill_state and drill_state.get('selected_county'):
            breadcrumbs.append(html.Span(" > ", className="breadcrumb-separator"))
            breadcrumbs.append(html.Span(drill_state['selected_county'], className="breadcrumb-item"))
        
        # Category level
        if drill_state and drill_state.get('selected_category'):
            breadcrumbs.append(html.Span(" > ", className="breadcrumb-separator"))
            breadcrumbs.append(html.Span(drill_state['selected_category'], className="breadcrumb-item"))
        
        # Metric level
        if drill_state and drill_state.get('selected_metric'):
            breadcrumbs.append(html.Span(" > ", className="breadcrumb-separator"))
            breadcrumbs.append(html.Span(f"{drill_state['selected_metric']} Analysis", className="breadcrumb-item active"))
        
        return breadcrumbs

    # Dynamic content update - FIXED to prevent state conflicts
    @app.callback(
        Output('dynamic-content', 'children'),
        [Input('drill-down-state', 'data')],
        prevent_initial_call=True
    )
    def update_dynamic_content(drill_state):
        print(f"DEBUG: update_dynamic_content called with: {drill_state}")
        
        if not drill_state:
            print(f"DEBUG: No drill state provided")
            return html.Div("No state information available.")
        
        level = drill_state.get('level', 'overview')
        print(f"DEBUG: Current level: {level}")
        
        if level == 'overview':
            return create_overview_layout(drill_state)
        elif level == 'category':
            return create_category_layout(drill_state)
        elif level == 'metric':
            # Extra validation for metric level
            required_fields = ['selected_state', 'selected_county', 'selected_category', 'selected_metric']
            missing = [field for field in required_fields if not drill_state.get(field)]
            
            if missing:
                print(f"DEBUG: Missing fields for metric layout: {missing}")
                print(f"DEBUG: Full state: {drill_state}")
                return html.Div([
                    html.H2("Metric Analysis - State Error", className="section-title"),
                    html.P(f"State management issue detected. Missing: {', '.join(missing)}"),
                    html.P(f"Current state: {drill_state}", style={"font-family": "monospace", "background": "#f0f0f0", "padding": "10px"}),
                    html.P("Try navigating back and clicking the sub-metric again.")
                ])
            
            return create_metric_layout(drill_state)
        
        return html.Div(f"Unknown level: {level}")

    # Main chart update
    @app.callback(
        Output('main-chart', 'figure'),
        [Input('drill-down-state', 'data')]
    )
    def update_main_chart(drill_state):
        print(f"DEBUG: Main chart update callback triggered")
        print(f"DEBUG: Drill state: {drill_state}")
        
        if not drill_state:
            return create_empty_chart("No state data")
        
        level = drill_state.get('level')
        selected_state = drill_state.get('selected_state')
        selected_county = drill_state.get('selected_county')
        selected_category = drill_state.get('selected_category')
        selected_metric = drill_state.get('selected_metric')
        
        if level == 'overview':
            # Main chart: County categories radar
            if selected_county and selected_state:
                return create_county_categories_radar(df, selected_state, selected_county)
            else:
                return create_empty_chart("Select a county to view category breakdown")
                
        elif level == 'category':
            # Main chart: Sub-metrics radar
            if selected_category and selected_county and selected_state:
                return create_sub_metrics_radar(df, selected_state, selected_county, selected_category)
            else:
                return create_empty_chart("Category information not available")
                
        elif level == 'metric':
            # Main chart: Metric analysis visualization
            if selected_metric and selected_category and selected_county and selected_state:
                return create_empty_chart(f"Metric Analysis: {selected_metric}")
            else:
                return create_empty_chart("Metric information not available")
        
        return create_empty_chart("")

    # Overview chart callback (only when in overview mode)
    @app.callback(
        [Output('overview-chart', 'figure'),
         Output('top-counties-chart', 'figure')],
        [Input('drill-down-state', 'data')],
        prevent_initial_call=True
    )
    def update_overview_charts(drill_state):
        level = drill_state.get('level') if drill_state else 'overview'
        
        if level == 'overview':
            # Overview chart: State performance
            overview_fig = create_state_overview_chart(df)
            
            # Top counties chart
            top_fig = create_top_counties_chart(df)
            
            return overview_fig, top_fig
        else:
            # Return empty charts for non-overview levels
            return create_empty_chart(""), create_empty_chart("")

    # Overview stats callback
    @app.callback(
        Output('overview-stats', 'children'),
        [Input('drill-down-state', 'data')],
        prevent_initial_call=True
    )
    def update_overview_stats(drill_state):
        level = drill_state.get('level') if drill_state else 'overview'
        
        if level == 'overview':
            selected_state = drill_state.get('selected_state') if drill_state else None
            selected_county = drill_state.get('selected_county') if drill_state else None
            
            if selected_county and selected_state:
                return create_county_overview_stats(df, selected_state, selected_county)
            else:
                return html.Div("Select a county to view statistics.")
        else:
            return html.Div()

    # Category-specific callbacks
    @app.callback(
        [Output('category-comparison-chart', 'figure'),
         Output('category-stats', 'children')],
        [Input('drill-down-state', 'data')],
        prevent_initial_call=True
    )
    def update_category_elements(drill_state):
        level = drill_state.get('level') if drill_state else 'overview'
        
        if level == 'category':
            selected_category = drill_state.get('selected_category') if drill_state else None
            selected_state = drill_state.get('selected_state') if drill_state else None
            selected_county = drill_state.get('selected_county') if drill_state else None
            
            if all([selected_category, selected_state, selected_county]):
                comparison_fig = create_category_comparison_chart(df, selected_state, selected_category, selected_county)
                stats = create_category_stats(df, selected_state, selected_county, selected_category)
                return comparison_fig, stats
            else:
                return create_empty_chart("Missing data"), html.Div("Missing data")
        else:
            return create_empty_chart(""), html.Div()

    # Metric-specific callbacks
    @app.callback(
        [Output('metric-distribution-chart', 'figure'),
         Output('peer-comparison-chart', 'figure'),
         Output('metric-insights', 'children')],
        [Input('drill-down-state', 'data')],
        prevent_initial_call=True
    )
    def update_metric_elements(drill_state):
        level = drill_state.get('level') if drill_state else 'overview'
        
        if level == 'metric':
            selected_metric = drill_state.get('selected_metric') if drill_state else None
            selected_category = drill_state.get('selected_category') if drill_state else None
            selected_state = drill_state.get('selected_state') if drill_state else None
            selected_county = drill_state.get('selected_county') if drill_state else None
            
            if all([selected_metric, selected_category, selected_state, selected_county]):
                full_metric_name = f"{selected_category}_{selected_metric}"
                
                # Verify the column exists
                if full_metric_name not in df.columns:
                    # Try case-insensitive match
                    possible_matches = [col for col in df.columns if col.lower() == full_metric_name.lower()]
                    if possible_matches:
                        full_metric_name = possible_matches[0]
                    else:
                        error_fig = create_empty_chart(f"Metric {full_metric_name} not found")
                        error_text = html.Div(f"Could not find metric: {full_metric_name}")
                        return error_fig, error_fig, error_text
                
                dist_fig = create_metric_distribution_chart(df, full_metric_name, selected_state, selected_county)
                peer_fig = create_peer_comparison_chart(df, full_metric_name, selected_state, selected_county)
                insights = create_metric_insights(df, full_metric_name, selected_state, selected_county)
                
                return dist_fig, peer_fig, insights
            else:
                empty_fig = create_empty_chart("Missing data")
                return empty_fig, empty_fig, html.Div("Missing data")
        else:
            empty_fig = create_empty_chart("")
            return empty_fig, empty_fig, html.Div()

    # Overview chart click callback (only for overview level)
    @app.callback(
        [Output('drill-down-state', 'data', allow_duplicate=True),
         Output('navigation-history', 'data', allow_duplicate=True)],
        [Input('overview-chart', 'clickData')],
        [State('drill-down-state', 'data'),
         State('navigation-history', 'data')],
        prevent_initial_call=True
    )
    def handle_overview_chart_clicks(overview_click, current_state, nav_history):
        if not nav_history:
            nav_history = []
        
        # Only handle if we're in overview mode and there's a click
        if not overview_click or not current_state or current_state.get('level') != 'overview':
            return current_state, nav_history
        
        new_state = dict(current_state)
        clicked_data = overview_click['points'][0]
        
        if 'x' in clicked_data:
            new_state['selected_state'] = clicked_data['x']
            new_state['selected_county'] = None
            new_state['selected_category'] = None
            new_state['selected_metric'] = None
        
        # Add to history if state changed
        if new_state != current_state:
            nav_history.append(new_state)
        
        return new_state, nav_history

    # Top counties chart click callback (only for overview level)
    @app.callback(
        [Output('drill-down-state', 'data', allow_duplicate=True),
         Output('navigation-history', 'data', allow_duplicate=True)],
        [Input('top-counties-chart', 'clickData')],
        [State('drill-down-state', 'data'),
         State('navigation-history', 'data')],
        prevent_initial_call=True
    )
    def handle_top_counties_chart_clicks(top_click, current_state, nav_history):
        if not nav_history:
            nav_history = []
        
        # Only handle if we're in overview mode and there's a click
        if not top_click or not current_state or current_state.get('level') != 'overview':
            return current_state, nav_history
        
        new_state = dict(current_state)
        clicked_data = top_click['points'][0]
        
        if 'x' in clicked_data:
            county_info = clicked_data['x'].split(', ')
            if len(county_info) == 2:
                new_state['selected_state'] = county_info[1]
                new_state['selected_county'] = county_info[0]
                new_state['selected_category'] = None
                new_state['selected_metric'] = None
        
        # Add to history if state changed
        if new_state != current_state:
            nav_history.append(new_state)
        
        return new_state, nav_history