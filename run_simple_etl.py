import pandas as pd
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_simple_etl(file_path, data_year=2023, data_source="County Data"):
    """Simple ETL function"""
    # Load data
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows")
    
    # Rename columns
    df = df.rename(columns={'FIPS': 'county_fips', 'State': 'state_name', 'County': 'county_name'})
    
    # Clean FIPS codes
    df['county_fips'] = df['county_fips'].astype(str).str.replace('.0', '').str.zfill(5)
    
    # Add state codes
    state_map = {'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA'}
    df['state_code'] = df['state_name'].map(state_map).fillna(df['state_name'].str[:2])
    
    # Clean county names
    df['county_name'] = df['county_name'].astype(str).str.title()
    
    # Remove rows with missing essential data
    df = df.dropna(subset=['county_fips', 'county_name', 'state_code'])
    
    logger.info(f"Cleaned data: {len(df)} rows")
    return df

# Test it
if __name__ == "__main__":
    result = run_simple_etl("RVN-3.csv")
    print(f"Processed {len(result)} counties successfully!")
    print(result[['county_fips', 'county_name', 'state_code']].head())