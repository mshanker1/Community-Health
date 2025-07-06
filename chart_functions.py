"""
Chart creation functions
"""
import plotly.graph_objects as go
import pandas as pd
from data_loader import (get_metric_categories, get_category_sub_metrics, 
                        get_overall_metrics, get_friendly_metric_name, parse_metric_name)

def create_empty_chart(message):
    """Create empty chart with message"""
    fig = go.Figure()
    if message:
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
    fig.update_layout(height=400)
    return fig

def create_county_categories_radar(df, state, county):
    """Create radar chart showing main categories for a county"""
    county_data = df[(df['State'] == state) & (df['County'] == county)]
    
    if county_data.empty:
        return create_empty_chart(f"No data found for {county}, {state}")
    
    county_data = county_data.iloc[0]
    
    categories = get_metric_categories()
    values = []
    
    for cat in categories:
        col_name = f"{cat}_Overall"
        if col_name in county_data.index and pd.notna(county_data[col_name]):
            values.append(county_data[col_name])
        else:
            values.append(0)  # Use 0 for missing data
    
    print(f"DEBUG: Creating county categories radar for {county}, {state}")
    print(f"DEBUG: Categories: {categories}")
    print(f"DEBUG: Values: {values}")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(54, 162, 235, 0.3)',
        line=dict(color='rgba(54, 162, 235, 0.8)', width=3),
        marker=dict(color='rgba(54, 162, 235, 0.8)', size=10),
        name=f"{county}, {state}",
        hovertemplate='<b>%{theta}</b><br>Score: %{r}%<br><i>Click to drill down</i><extra></extra>',
        mode='lines+markers'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=12),
                gridcolor='#e0e0e0',
                tick0=0,
                dtick=20
            ),
            angularaxis=dict(
                tickfont=dict(size=14, family="Arial Black"),
                gridcolor='#e0e0e0',
                linecolor='#666',
                direction='clockwise',
                rotation=90
            )
        ),
        title=f"Main Categories: {county}, {state}<br><sup>Click on any segment to drill down</sup>",
        title_font_size=16,
        height=500,
        margin=dict(t=80, b=60, l=60, r=60),
        clickmode='event+select'
    )
    
    return fig

def create_sub_metrics_radar(df, state, county, category):
    """Create radar chart showing sub-metrics for a category with enhanced debugging"""
    from data_loader import debug_column_structure
    
    print(f"DEBUG: === CREATING SUB-METRICS RADAR ===")
    print(f"DEBUG: State: {state}, County: {county}, Category: {category}")
    
    # Debug the column structure for this category
    debug_column_structure(df, category)
    
    county_data = df[(df['State'] == state) & (df['County'] == county)]
    if county_data.empty:
        print(f"DEBUG: ERROR - No data found for {county}, {state}")
        return create_empty_chart(f"No data found for {county}, {state}")
    
    county_data = county_data.iloc[0]
    
    sub_metrics = get_category_sub_metrics(df, category)
    print(f"DEBUG: Sub-metrics found for {category}: {sub_metrics}")
    
    if not sub_metrics:
        return create_empty_chart(f"No sub-metrics found for {category}")
    
    # Create mapping and validate data
    valid_data = []
    display_names = []
    column_mapping = {}  # Track which display name maps to which column
    
    for col in sub_metrics:
        print(f"DEBUG: Processing column: {col}")
        
        if col in county_data.index:
            value = county_data[col]
            print(f"DEBUG: Column {col} has value: {value}")
            
            if pd.notna(value):
                friendly_name = get_friendly_metric_name(col)
                valid_data.append(value)
                display_names.append(friendly_name)
                column_mapping[friendly_name] = col
                print(f"DEBUG: Added {col} -> '{friendly_name}' = {value}")
            else:
                print(f"DEBUG: Skipped {col} (NaN value)")
        else:
            print(f"DEBUG: Skipped {col} (not in county data)")
    
    if not valid_data:
        return create_empty_chart(f"No valid data for {category} sub-metrics")
    
    print(f"DEBUG: Final display names: {display_names}")
    print(f"DEBUG: Final values: {valid_data}")
    print(f"DEBUG: Column mapping for clicks: {column_mapping}")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=valid_data + [valid_data[0]] if valid_data else [],
        theta=display_names + [display_names[0]] if display_names else [],
        fill='toself',
        fillcolor='rgba(255, 99, 132, 0.3)',
        line=dict(color='rgba(255, 99, 132, 0.8)', width=3),
        marker=dict(color='rgba(255, 99, 132, 0.8)', size=10),
        name=f"{category} Sub-metrics",
        hovertemplate="<b>%{theta}</b><br>Score: %{r}%<br><i>Click for detailed analysis</i><extra></extra>",
        mode='lines+markers'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=12),
                gridcolor='#e0e0e0',
                tick0=0,
                dtick=20
            ),
            angularaxis=dict(
                tickfont=dict(size=12, family="Arial Black"),
                gridcolor='#e0e0e0',
                linecolor='#666',
                direction='clockwise',
                rotation=90
            )
        ),
        title=f"{category} Sub-metrics: {county}, {state}<br><sup>Click on any segment for detailed analysis</sup>",
        title_font_size=16,
        height=500,
        margin=dict(t=80, b=60, l=60, r=60),
        clickmode='event+select'
    )
    
    print(f"DEBUG: === RADAR CHART CREATED SUCCESSFULLY ===")
    return fig

def create_state_overview_chart(df):
    """Create state-level overview bar chart"""
    overall_metrics = get_overall_metrics()
    
    # Check if all required columns exist
    existing_metrics = [col for col in overall_metrics if col in df.columns]
    if not existing_metrics:
        return create_empty_chart("No overall metric columns found")
    
    state_summary = df.groupby('State')[existing_metrics].mean().round(1)
    state_summary['Average'] = state_summary.mean(axis=1).round(1)
    state_summary = state_summary.sort_values('Average', ascending=False)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=state_summary.index,
        y=state_summary['Average'],
        name='Average Score',
        marker_color='rgba(54, 162, 235, 0.8)',
        hovertemplate='<b>%{x}</b><br>Average Score: %{y}%<br><i>Click to filter by state</i><extra></extra>'
    ))
    
    fig.update_layout(
        title="State Performance Overview (Click to Filter)",
        xaxis_title="State",
        yaxis_title="Average Percentile Score",
        yaxis=dict(range=[0, 100]),
        height=400
    )
    
    return fig

def create_top_counties_chart(df):
    """Create chart showing top performing counties across all states"""
    overall_metrics = get_overall_metrics()
    
    # Check if all required columns exist
    existing_metrics = [col for col in overall_metrics if col in df.columns]
    if not existing_metrics:
        return create_empty_chart("No overall metric columns found")
    
    df_copy = df.copy()
    df_copy['Average'] = df_copy[existing_metrics].mean(axis=1).round(1)
    top_counties = df_copy.nlargest(10, 'Average')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"{row['County']}, {row['State']}" for _, row in top_counties.iterrows()],
        y=top_counties['Average'],
        name='Top Counties',
        marker_color='rgba(255, 99, 132, 0.8)',
        hovertemplate='<b>%{x}</b><br>Average Score: %{y}%<br><i>Click to drill down</i><extra></extra>'
    ))
    
    fig.update_layout(
        title="Top 10 Performing Counties (Click to Drill Down)",
        xaxis_title="County, State",
        yaxis_title="Average Percentile Score",
        yaxis=dict(range=[0, 100]),
        height=400,
        xaxis_tickangle=-45
    )
    
    return fig

def create_category_comparison_chart(df, state, category, selected_county):
    """Create comparison chart of category performance across counties in state"""
    state_data = df[df['State'] == state].copy()
    category_col = f"{category}_Overall"
    
    if category_col not in df.columns:
        return create_empty_chart(f"Column {category_col} not found")
    
    # Remove rows with missing data for this category
    state_data = state_data.dropna(subset=[category_col])
    
    if state_data.empty:
        return create_empty_chart(f"No data for {category} in {state}")
    
    state_data = state_data.sort_values(category_col, ascending=True)
    
    # Highlight selected county
    colors = ['red' if county == selected_county else 'rgba(54, 162, 235, 0.6)' 
              for county in state_data['County']]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=state_data['County'],
        x=state_data[category_col],
        orientation='h',
        marker_color=colors,
        hovertemplate='<b>%{y}</b><br>' + f'{category}: %{{x}}%<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{category} Rankings in {state}",
        xaxis_title=f"{category} Score",
        yaxis_title="County",
        height=400,
        margin=dict(l=120)
    )
    
    return fig

def create_metric_distribution_chart(df, metric_col, state, county):
    """Create distribution chart for the selected metric"""
    if metric_col not in df.columns:
        return create_empty_chart(f"Metric {metric_col} not found")
    
    # Get national distribution
    national_values = df[metric_col].dropna()
    
    if national_values.empty:
        return create_empty_chart(f"No data available for {metric_col}")
    
    # Get county value
    county_data = df[(df['State'] == state) & (df['County'] == county)]
    if county_data.empty or metric_col not in county_data.columns:
        return create_empty_chart(f"No data for {county}, {state}")
    
    county_value = county_data[metric_col].iloc[0]
    
    if pd.isna(county_value):
        return create_empty_chart(f"No {metric_col} data for {county}, {state}")
    
    fig = go.Figure()
    
    # Add histogram
    fig.add_trace(go.Histogram(
        x=national_values,
        nbinsx=20,
        name='All Counties',
        marker_color='rgba(54, 162, 235, 0.6)',
        hovertemplate='Range: %{x}<br>Count: %{y}<extra></extra>'
    ))
    
    # Add vertical line for selected county
    fig.add_vline(
        x=county_value,
        line_dash="dash",
        line_color="red",
        line_width=3,
        annotation_text=f"{county}, {state}: {county_value:.1f}%",
        annotation_position="top"
    )
    
    metric_name = parse_metric_name(metric_col)[1]
    fig.update_layout(
        title=f"National Distribution of {metric_name} Scores",
        xaxis_title=f"{metric_name} Percentile Score",
        yaxis_title="Number of Counties",
        height=400
    )
    
    return fig

def create_peer_comparison_chart(df, metric_col, state, county):
    """Create peer comparison chart with enhanced peer selection criteria"""
    if metric_col not in df.columns:
        return create_empty_chart(f"Metric {metric_col} not found")
    
    # Get county value
    county_data = df[(df['State'] == state) & (df['County'] == county)]
    if county_data.empty:
        return create_empty_chart(f"No data for {county}, {state}")
    
    county_value = county_data[metric_col].iloc[0]
    
    if pd.isna(county_value):
        return create_empty_chart(f"No {metric_col} data for {county}, {state}")
    
    # Enhanced peer selection with multiple criteria
    df_copy = df.copy()
    
    # Extract category from metric name for category-specific similarity
    metric_category = parse_metric_name(metric_col)[0]
    category_overall_col = f"{metric_category}_Overall"
    
    print(f"DEBUG: Peer selection for {county}, {state}")
    print(f"DEBUG: Metric: {metric_col}, Category: {metric_category}")
    
    # Get selected county's characteristics for comparison
    selected_county_row = county_data.iloc[0]
    
    # 1. POPULATION SIMILARITY (if population data exists)
    population_cols = [col for col in df.columns if 'population' in col.lower() or 'pop' in col.lower()]
    county_population = None
    if population_cols:
        pop_col = population_cols[0]  # Use first population column found
        if pop_col in selected_county_row.index and pd.notna(selected_county_row[pop_col]):
            county_population = selected_county_row[pop_col]
            print(f"DEBUG: County population: {county_population}")
    
    # 2. CATEGORY-SPECIFIC PERFORMANCE SIMILARITY
    county_category_score = None
    if category_overall_col in selected_county_row.index and pd.notna(selected_county_row[category_overall_col]):
        county_category_score = selected_county_row[category_overall_col]
        print(f"DEBUG: County {metric_category} score: {county_category_score}")
    
    # 3. GEOGRAPHIC PROXIMITY (using state-level grouping for now)
    # Note: For true geographic proximity, we'd need lat/lon coordinates
    same_state_counties = df_copy[df_copy['State'] == state]
    
    # Start with different selection strategies and combine results
    peer_candidates = []
    
    # Strategy 1: Same state peers (highest priority)
    if len(same_state_counties) > 1:  # More than just the selected county
        same_state_peers = same_state_counties[
            ~((same_state_counties['State'] == state) & (same_state_counties['County'] == county)) &
            same_state_counties[metric_col].notna()
        ]
        
        # If we have category scores, filter by category similarity within state
        if county_category_score is not None and category_overall_col in same_state_peers.columns:
            category_similar = same_state_peers[
                abs(same_state_peers[category_overall_col] - county_category_score) <= 15
            ]
            peer_candidates.extend([('same_state_category', row) for _, row in category_similar.head(5).iterrows()])
            print(f"DEBUG: Found {len(category_similar)} same-state category-similar peers")
        
        # Add other same-state counties even if not category-similar
        other_same_state = same_state_peers.head(3)
        peer_candidates.extend([('same_state', row) for _, row in other_same_state.iterrows()])
        print(f"DEBUG: Added {len(other_same_state)} other same-state peers")
    
    # Strategy 2: Category-specific similarity (nationwide)
    if county_category_score is not None and category_overall_col in df_copy.columns:
        category_peers = df_copy[
            (abs(df_copy[category_overall_col] - county_category_score) <= 10) &
            ~((df_copy['State'] == state) & (df_copy['County'] == county)) &
            df_copy[metric_col].notna()
        ]
        
        # Prioritize different states to add geographic diversity
        different_state_category_peers = category_peers[category_peers['State'] != state].head(4)
        peer_candidates.extend([('category_similar', row) for _, row in different_state_category_peers.iterrows()])
        print(f"DEBUG: Found {len(different_state_category_peers)} nationwide category-similar peers")
    
    # Strategy 3: Population similarity (if population data available)
    if county_population is not None and population_cols:
        pop_col = population_cols[0]
        # Define population similarity ranges (±25% of county population)
        pop_range = county_population * 0.25
        pop_similar = df_copy[
            (abs(df_copy[pop_col] - county_population) <= pop_range) &
            ~((df_copy['State'] == state) & (df_copy['County'] == county)) &
            df_copy[metric_col].notna() &
            df_copy[pop_col].notna()
        ]
        
        # Prefer different states for diversity
        different_state_pop_peers = pop_similar[pop_similar['State'] != state].head(3)
        peer_candidates.extend([('population_similar', row) for _, row in different_state_pop_peers.iterrows()])
        print(f"DEBUG: Found {len(different_state_pop_peers)} population-similar peers")
    
    # Strategy 4: Overall performance similarity (fallback)
    overall_metrics = get_overall_metrics()
    existing_overall_metrics = [col for col in overall_metrics if col in df.columns]
    
    if existing_overall_metrics:
        df_copy['Average'] = df_copy[existing_overall_metrics].mean(axis=1)
        county_avg = df_copy[(df_copy['State'] == state) & (df_copy['County'] == county)]['Average'].iloc[0]
        
        overall_similar = df_copy[
            (abs(df_copy['Average'] - county_avg) <= 8) &
            ~((df_copy['State'] == state) & (df_copy['County'] == county)) &
            df_copy[metric_col].notna()
        ]
        
        # Add a few overall-similar peers from different states
        different_state_overall_peers = overall_similar[overall_similar['State'] != state].head(2)
        peer_candidates.extend([('overall_similar', row) for _, row in different_state_overall_peers.iterrows()])
        print(f"DEBUG: Found {len(different_state_overall_peers)} overall-similar peers")
    
    # Remove duplicates and select final peer set
    seen_counties = set()
    final_peers = []
    peer_labels = []
    
    # Prioritize peers: same_state_category > same_state > category_similar > population_similar > overall_similar
    priority_order = ['same_state_category', 'same_state', 'category_similar', 'population_similar', 'overall_similar']
    
    for priority in priority_order:
        for peer_type, row in peer_candidates:
            if peer_type == priority:
                county_key = (row['State'], row['County'])
                if county_key not in seen_counties and len(final_peers) < 10:
                    seen_counties.add(county_key)
                    final_peers.append(row)
                    peer_labels.append(peer_type)
    
    print(f"DEBUG: Final peer selection: {len(final_peers)} peers")
    for i, (peer, label) in enumerate(zip(final_peers, peer_labels)):
        print(f"DEBUG:   {i+1}. {peer['County']}, {peer['State']} ({label})")
    
    # Create comparison dataframe
    if not final_peers:
        return create_empty_chart("No suitable peer counties found")
    
    comparison_data = pd.DataFrame(final_peers)
    
    # Add the selected county back
    selected_county_data = df_copy[(df_copy['State'] == state) & (df_copy['County'] == county)]
    comparison_data = pd.concat([comparison_data, selected_county_data], ignore_index=True)
    
    # Remove any rows with missing metric data
    comparison_data = comparison_data.dropna(subset=[metric_col])
    
    if comparison_data.empty:
        return create_empty_chart("No peer data available for comparison")
    
    # Create color coding based on peer type
    colors = []
    for _, row in comparison_data.iterrows():
        if row['State'] == state and row['County'] == county:
            colors.append('red')  # Selected county
        elif row['State'] == state:
            colors.append('rgba(54, 162, 235, 0.9)')  # Same state - blue
        else:
            colors.append('rgba(75, 192, 192, 0.8)')  # Different state - teal
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"{row['County']}, {row['State']}" for _, row in comparison_data.iterrows()],
        y=comparison_data[metric_col],
        marker_color=colors,
        hovertemplate='<b>%{x}</b><br>' + f'{parse_metric_name(metric_col)[1]}: %{{y}}%<br>' +
                     '<i>%{customdata}</i><extra></extra>',
        customdata=[
            'Selected County' if (row['State'] == state and row['County'] == county) 
            else f"Same State" if row['State'] == state 
            else f"Peer County" 
            for _, row in comparison_data.iterrows()
        ]
    ))
    
    metric_name = parse_metric_name(metric_col)[1]
    fig.update_layout(
        title=f"Peer Comparison: {metric_name} Scores<br><sub>Red: Selected County | Blue: Same State | Teal: Similar Peers</sub>",
        xaxis_title="County, State",
        yaxis_title=f"{metric_name} Percentile Score",
        height=400,
        xaxis_tickangle=-45
    )
    
    return fig