"""
Data loading and processing utilities
"""
import pandas as pd
import numpy as np

def load_data():
    """
    Load and process the hierarchical county well-being data from Sheet2.csv
    """
    try:
        # Read the actual CSV file
        df = pd.read_csv('Sheet2.csv')
        print(f"DEBUG: Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        print(f"DEBUG: Columns: {df.columns.tolist()}")
        
        # Clean column names (remove any extra spaces)
        df.columns = df.columns.str.strip()
        
        # Ensure all metric columns are properly processed
        percentage_columns = [col for col in df.columns if col not in ['FIPS', 'State', 'County']]
        
        for col in percentage_columns:
            # Handle percentage values and errors
            df[col] = df[col].astype(str).str.replace('%', '').replace('#DIV/0!', '').replace('nan', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with missing FIPS, State, or County
        df = df.dropna(subset=['FIPS', 'State', 'County'])
        
        # Remove rows where all main category overall scores are missing
        main_categories = ['Health_Overall', 'Wealth_Overall', 'Education_Overall', 'Community_Overall']
        df = df.dropna(subset=main_categories, how='all')
        
        print(f"DEBUG: After cleaning: {len(df)} rows")
        print(f"DEBUG: Sample data:")
        print(df[['State', 'County', 'Health_Overall', 'Wealth_Overall', 'Education_Overall', 'Community_Overall']].head())
        
        return df
        
    except FileNotFoundError:
        print("ERROR: Sheet2.csv not found. Please ensure the file is in the same directory as the script.")
        # Return empty dataframe with expected structure
        return pd.DataFrame(columns=['FIPS', 'State', 'County', 'Health_Overall', 'Wealth_Overall', 'Education_Overall', 'Community_Overall'])
    
    except Exception as e:
        print(f"ERROR loading data: {e}")
        # Return empty dataframe with expected structure
        return pd.DataFrame(columns=['FIPS', 'State', 'County', 'Health_Overall', 'Wealth_Overall', 'Education_Overall', 'Community_Overall'])

def get_metric_categories():
    """Get the main metric categories"""
    return ['Health', 'Wealth', 'Education', 'Community']

def get_category_metrics(df, category):
    """Get all metric columns for a specific category"""
    pattern = f"{category}_"
    return [col for col in df.columns if col.startswith(pattern)]

def get_category_sub_metrics(df, category):
    """Get sub-metrics for a category (excluding _Overall)"""
    metrics = get_category_metrics(df, category)
    return [col for col in metrics if not col.endswith('_Overall')]

def get_overall_metrics():
    """Get the overall metric columns"""
    return [f"{cat}_Overall" for cat in get_metric_categories()]

def parse_metric_name(column_name):
    """Parse metric column name into category and sub-metric"""
    if '_' in column_name:
        parts = column_name.split('_', 1)
        return parts[0], parts[1]
    return column_name, ''

def get_friendly_metric_name(column_name):
    """Convert column names to friendly display names with better mapping"""
    
    # More comprehensive name mapping
    name_mapping = {
        # Health metrics
        'Length_of_Life': 'Length of Life',
        'Quality_of_Life': 'Quality of Life', 
        'Health_Behaviors': 'Health Behaviors',
        'Health_Resources': 'Health Resources',
        'Life_Expectancy': 'Life Expectancy',
        
        # Wealth metrics
        'Income': 'Income',
        'Housing': 'Housing',
        'Income_Ratio': 'Income Ratio',
        'Child_Poverty': 'Child Poverty',
        
        # Education metrics
        'School_Spending': 'School Spending',
        'High_School': 'High School',
        'Associate_Degree': 'Associate Degree',
        'College_Degree': 'College Degree',
        'Advanced_Degree': 'Advanced Degree',
        
        # Community metrics
        'Severe_Housing_Problems': 'Housing Problems',
        'Food_Insecurity': 'Food Insecurity',
        'Long_Commute': 'Long Commute',
        'Residential_Internet_Service': 'Internet Access',
        'Violent_Crime_Rate': 'Crime Rate',
        'Parks_Access': 'Parks Access'
    }
    
    # Parse the column name
    if '_' in column_name:
        category, metric = column_name.split('_', 1)
        # Return mapped name or fallback to cleaned version
        return name_mapping.get(metric, metric.replace('_', ' '))
    else:
        # For columns without underscore, return as-is with spaces
        return name_mapping.get(column_name, column_name.replace('_', ' '))

def create_display_to_column_mapping(df, category):
    """Create a mapping from display names back to column names for a specific category"""
    sub_metrics = get_category_sub_metrics(df, category)
    mapping = {}
    
    print(f"DEBUG: Creating display mapping for category '{category}'")
    
    for col in sub_metrics:
        friendly_name = get_friendly_metric_name(col)
        mapping[friendly_name] = col
        print(f"DEBUG: Display mapping: '{friendly_name}' -> '{col}'")
    
    print(f"DEBUG: Final mapping for {category}: {mapping}")
    return mapping

def debug_column_structure(df, category=None):
    """Debug function to examine column structure"""
    print(f"DEBUG: === COLUMN STRUCTURE DEBUG ===")
    print(f"DEBUG: Total columns in dataframe: {len(df.columns)}")
    
    if category:
        print(f"DEBUG: Columns for category '{category}':")
        category_cols = [col for col in df.columns if col.startswith(f"{category}_")]
        for col in category_cols:
            friendly = get_friendly_metric_name(col)
            print(f"DEBUG:   {col} -> '{friendly}'")
    else:
        print(f"DEBUG: All metric columns:")
        for cat in get_metric_categories():
            print(f"DEBUG: {cat} columns:")
            cat_cols = [col for col in df.columns if col.startswith(f"{cat}_")]
            for col in cat_cols:
                friendly = get_friendly_metric_name(col)
                print(f"DEBUG:   {col} -> '{friendly}'")
    
    print(f"DEBUG: === END COLUMN STRUCTURE DEBUG ===")
    return True