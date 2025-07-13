import pandas as pd
import sqlite3
import os

def create_database_from_csv(csv_file='RVN3.csv', db_file='county_health.db'):
    """
    Create SQLite database from the CSV file with proper data types
    """
    
    # Check if database already exists
    if os.path.exists(db_file):
        print(f"Database {db_file} already exists. Backing it up...")
        import shutil
        shutil.copy(db_file, f"{db_file}.backup")
        os.remove(db_file)
    
    # Read the CSV file
    print(f"Reading {csv_file}...")
    df = pd.read_csv(csv_file)
    
    # Print basic info about the data
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    print("\nFirst few columns:", df.columns[:10].tolist())
    print("\nData types:", df.dtypes.head())
    
    # Create connection to SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create the main data table
    print(f"\nCreating table 'county_data' in {db_file}...")
    
    # Write the dataframe to SQLite
    # This will automatically create the table with appropriate column types
    df.to_sql('county_data', conn, if_exists='replace', index=False)
    
    # Create additional tables that the dashboard expects
    print("Creating additional tables...")
    
    # Create counties table for the dropdown
    # First, drop the existing counties table if it exists
    cursor.execute("DROP TABLE IF EXISTS counties")
    
    # Create counties table with proper data
    cursor.execute("""
        CREATE TABLE counties AS
        SELECT 
            CAST(FIPS AS INTEGER) as fips_code,
            County as county_name,
            State as state_code,
            State as state_name
        FROM county_data
        WHERE FIPS IS NOT NULL 
          AND County IS NOT NULL 
          AND State IS NOT NULL
        ORDER BY State, County
    """)
    
    # Create an index on FIPS for faster lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fips ON county_data(FIPS)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_counties_fips ON counties(fips_code)")
    
    # Create a computed_metrics table that matches the original expected structure
    # This is a view that transforms the column-based data into row-based metrics
    print("Creating computed_metrics view...")
    
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS computed_metrics AS
        WITH metric_values AS (
            -- Society metrics
            SELECT FIPS as county_fips, 
                   'SOCIETY' as top_level,
                   'HEALTH' as sub_category,
                   'Health Score' as metric_name,
                   Society_HEALTH as metric_value,
                   50.0 as percentile_rank
            FROM county_data
            WHERE Society_HEALTH IS NOT NULL
            
            UNION ALL
            
            SELECT FIPS, 'SOCIETY', 'WEALTH', 'Wealth Score', 
                   Society_WEALTH, 50.0
            FROM county_data
            WHERE Society_WEALTH IS NOT NULL
            
            UNION ALL
            
            SELECT FIPS, 'SOCIETY', 'EDUCATIONINDEX', 'Education Index', 
                   Society_EDUCATIONINDEX, 50.0
            FROM county_data
            WHERE Society_EDUCATIONINDEX IS NOT NULL
            
            UNION ALL
            
            SELECT FIPS, 'SOCIETY', 'COMMUNITYINDEX', 'Community Index', 
                   Society_COMMUNITYINDEX, 50.0
            FROM county_data
            WHERE Society_COMMUNITYINDEX IS NOT NULL
            
            UNION ALL
            
            SELECT FIPS, 'SOCIETY', 'POPULATION', 'Population Score', 
                   Society_POPULATION, 50.0
            FROM county_data
            WHERE Society_POPULATION IS NOT NULL
            
            -- Economy metrics
            UNION ALL
            
            SELECT FIPS, 'ECONOMY', 'BUSINESS', 'Business Score', 
                   Economy_Business, 50.0
            FROM county_data
            WHERE Economy_Business IS NOT NULL
            
            UNION ALL
            
            SELECT FIPS, 'ECONOMY', 'GOVERNMENT', 'Government Score', 
                   Economy_GOVERNMENT, 50.0
            FROM county_data
            WHERE Economy_GOVERNMENT IS NOT NULL
            
            UNION ALL
            
            SELECT FIPS, 'ECONOMY', 'NON-PROFIT', 'Non-Profit Score', 
                   "Economy_NON-PROFIT", 50.0
            FROM county_data
            WHERE "Economy_NON-PROFIT" IS NOT NULL
            
            UNION ALL
            
            SELECT FIPS, 'ECONOMY', 'EMPLOYMENT', 'Employment Score', 
                   Economy_EMPLOYMENT, 50.0
            FROM county_data
            WHERE Economy_EMPLOYMENT IS NOT NULL
            
            UNION ALL
            
            SELECT FIPS, 'ECONOMY', 'ENERGY', 'Energy Score', 
                   Economy_ENERGY, 50.0
            FROM county_data
            WHERE Economy_ENERGY IS NOT NULL
            
            -- Nature metrics
            UNION ALL
            
            SELECT FIPS, 'NATURE', 'PLANET', 'Planet Score', 
                   Nature_PLANET, 50.0
            FROM county_data
            WHERE Nature_PLANET IS NOT NULL
        )
        SELECT * FROM metric_values
    """)
    
    # Verify the data
    print("\nVerifying data...")
    
    # Check counties table
    county_count = cursor.execute("SELECT COUNT(*) FROM counties").fetchone()[0]
    print(f"Counties table has {county_count} rows")
    
    # Check sample data
    print("\nSample counties:")
    sample_counties = cursor.execute("SELECT * FROM counties LIMIT 5").fetchall()
    for county in sample_counties:
        print(f"  {county}")
    
    # Check metric counts by category
    print("\nMetric counts by category:")
    metric_counts = cursor.execute("""
        SELECT top_level, COUNT(DISTINCT sub_category) as sub_categories
        FROM computed_metrics
        GROUP BY top_level
    """).fetchall()
    for category, count in metric_counts:
        print(f"  {category}: {count} sub-categories")
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"\nDatabase {db_file} created successfully!")
    
    # Print instructions for percentile calculation
    print("\nNote: The percentile_rank values are set to 50.0 as placeholders.")
    print("To calculate actual percentiles, you would need to:")
    print("1. Compute the distribution of each metric across all counties")
    print("2. Calculate the percentile rank for each county's value")
    print("3. Update the computed_metrics view or create a separate percentiles table")

def calculate_percentiles(db_file='county_health.db'):
    """
    Optional: Calculate actual percentile ranks for each metric
    """
    conn = sqlite3.connect(db_file)
    
    print("\nCalculating percentile ranks...")
    
    # Get all metric columns
    df = pd.read_sql("SELECT * FROM county_data", conn)
    
    # List of metric columns (excluding FIPS, State, County)
    metric_columns = [col for col in df.columns if col not in ['FIPS', 'State', 'County']]
    
    # Create a table to store percentile ranks
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metric_percentiles (
            county_fips REAL,
            metric_name TEXT,
            metric_value REAL,
            percentile_rank REAL,
            PRIMARY KEY (county_fips, metric_name)
        )
    """)
    
    # Calculate percentiles for each metric
    for col in metric_columns:
        print(f"  Processing {col}...")
        
        # Get non-null values
        valid_data = df[['FIPS', col]].dropna()
        
        if len(valid_data) > 0:
            # Calculate percentile ranks
            valid_data['percentile_rank'] = valid_data[col].rank(pct=True) * 100
            
            # Insert into table
            for _, row in valid_data.iterrows():
                cursor.execute("""
                    INSERT OR REPLACE INTO metric_percentiles 
                    (county_fips, metric_name, metric_value, percentile_rank)
                    VALUES (?, ?, ?, ?)
                """, (row['FIPS'], col, row[col], row['percentile_rank']))
    
    conn.commit()
    conn.close()
    
    print("Percentile calculations complete!")

if __name__ == "__main__":
    # Create the database
    create_database_from_csv()
    
    # Optionally calculate percentiles
    # calculate_percentiles()
