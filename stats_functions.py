"""
Statistics and insights functions
"""
import pandas as pd
from dash import html
from data_loader import (get_metric_categories, get_category_sub_metrics, 
                        parse_metric_name)

def create_county_overview_stats(df, state, county):
    """Create statistics cards for county overview"""
    county_data = df[(df['State'] == state) & (df['County'] == county)].iloc[0]
    categories = get_metric_categories()
    
    cards = html.Div([
        html.H3(f"Category Scores for {county}, {state}", className="section-title"),
        html.Div([
            html.Div([
                html.H4(f"{county_data[f'{cat}_Overall']:.1f}%", className="stat-value"),
                html.P(cat, className="stat-label")
            ], className=f"stat-card {cat.lower()}")
            for cat in categories
        ], className="stats-grid")
    ])
    
    return cards

def create_category_stats(df, state, county, category):
    """Create statistics cards for category detail view"""
    county_data = df[(df['State'] == state) & (df['County'] == county)].iloc[0]
    
    # Get sub-metrics for this category
    sub_metrics = get_category_sub_metrics(df, category)
    overall_col = f"{category}_Overall"
    
    # Calculate state averages for comparison
    state_data = df[df['State'] == state]
    state_avg_overall = state_data[overall_col].mean()
    
    cards = html.Div([
        html.H3(f"{category} Performance Analysis", className="section-title"),
        
        # Overall category performance
        html.Div([
            html.Div([
                html.H4(f"{county_data[overall_col]:.1f}%", className="stat-value"),
                html.P(f"{category} Overall", className="stat-label"),
                html.P(f"{county_data[overall_col] - state_avg_overall:+.1f} vs state avg", 
                       className=f"comparison-text {'positive' if county_data[overall_col] > state_avg_overall else 'negative'}")
            ], className=f"stat-card {category.lower()}")
        ], className="stats-grid"),
        
        # Sub-metrics performance
        html.H4("Sub-metric Breakdown:", className="section-subtitle"),
        html.Div([
            html.Div([
                html.H4(f"{county_data[col]:.1f}%", className="stat-value"),
                html.P(parse_metric_name(col)[1], className="stat-label")
            ], className="stat-card sub-metric")
            for col in sub_metrics if col in county_data.index and pd.notna(county_data[col])
        ], className="stats-grid")
    ])
    
    return cards

def create_metric_insights(df, metric_col, state, county):
    """Create insights panel for the selected metric"""
    if metric_col not in df.columns:
        return html.Div(f"Metric {metric_col} not found in data")
    
    county_value = df[(df['State'] == state) & (df['County'] == county)][metric_col].iloc[0]
    national_avg = df[metric_col].mean()
    state_avg = df[df['State'] == state][metric_col].mean()
    
    # Calculate percentile rank
    percentile_rank = (df[metric_col] < county_value).mean() * 100
    
    metric_name = parse_metric_name(metric_col)[1]
    category = parse_metric_name(metric_col)[0]
    
    insights = html.Div([
        html.H3(f"{metric_name} Analysis for {county}, {state}", className="section-title"),
        html.Div([
            html.Div([
                html.H4(f"{county_value:.1f}%", className="insight-value"),
                html.P("County Score", className="insight-label")
            ], className="insight-card"),
            
            html.Div([
                html.H4(f"{percentile_rank:.0f}th", className="insight-value"),
                html.P("National Percentile", className="insight-label")
            ], className="insight-card"),
            
            html.Div([
                html.H4(f"{county_value - national_avg:+.1f}", className="insight-value"),
                html.P("vs National Avg", className="insight-label")
            ], className="insight-card"),
            
            html.Div([
                html.H4(f"{county_value - state_avg:+.1f}", className="insight-value"),
                html.P("vs State Avg", className="insight-label")
            ], className="insight-card")
        ], className="insights-grid"),
        
        # Additional context
        html.Div([
            html.P(f"This metric is part of the {category} category.", className="context-text"),
            html.P(f"National range: {df[metric_col].min():.1f}% - {df[metric_col].max():.1f}%", className="context-text"),
            html.P(f"State range: {df[df['State'] == state][metric_col].min():.1f}% - {df[df['State'] == state][metric_col].max():.1f}%", className="context-text")
        ], className="context-panel")
    ])
    
    return insights