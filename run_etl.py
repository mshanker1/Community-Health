from county_health_etl import CountyHealthETL
import sys

# Initialize ETL pipeline
etl = CountyHealthETL()

# Replace with your actual file path
data_file = "RVN-2.csv"  # Change this to your file name
data_year = 2023  # Change this to your data year
data_source = "County Health Dashboard Data"  # Change this to your source name

try:
    print(f"Starting ETL pipeline for {data_file}...")
    result_df = etl.run_pipeline(data_file, data_year, data_source)
    
    print(f"\n✅ SUCCESS: Processed {len(result_df)} counties")
    print(f"📊 Database created: county_health.db")
    print(f"🏛️ Counties processed: {result_df['county_name'].nunique()}")
    print(f"📍 States included: {result_df['state_code'].nunique()}")
    
    # Show sample of results
    print("\n📋 Sample of processed data:")
    print(result_df[['county_fips', 'county_name', 'state_code']].head())
    
except FileNotFoundError:
    print(f"❌ ERROR: File '{data_file}' not found")
    print("Please check the file path and try again.")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    sys.exit(1)