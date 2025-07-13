import sqlite3
import pandas as pd
import os

def test_database(db_file='county_health.db'):
    """Test the SQLite database to see what's in it"""
    
    print(f"Testing database: {db_file}")
    print(f"Database exists: {os.path.exists(db_file)}")
    
    if not os.path.exists(db_file):
        print("ERROR: Database file not found!")
        return
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # List all tables
        print("\n=== TABLES IN DATABASE ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # For each table, show structure and sample data
        for table in tables:
            table_name = table[0]
            print(f"\n=== TABLE: {table_name} ===")
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print("Columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")
            
            # Show sample data
            if count > 0:
                print("Sample data (first 3 rows):")
                df = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 3", conn)
                print(df)
        
        # Test specific queries used by the dashboard
        print("\n=== TESTING DASHBOARD QUERIES ===")
        
        # Test counties query
        try:
            print("\nTesting counties query...")
            counties_df = pd.read_sql("""
                SELECT fips_code, county_name, state_code, state_name
                FROM counties 
                LIMIT 5
            """, conn)
            print(f"Success! Found {len(counties_df)} counties")
            print(counties_df)
        except Exception as e:
            print(f"Failed: {e}")
            
            # Try alternative query
            try:
                print("\nTrying alternative query on county_data...")
                counties_df = pd.read_sql("""
                    SELECT FIPS as fips_code, County as county_name, State as state_code
                    FROM county_data 
                    LIMIT 5
                """, conn)
                print(f"Success with county_data! Found {len(counties_df)} counties")
                print(counties_df)
            except Exception as e2:
                print(f"Also failed: {e2}")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR connecting to database: {e}")

if __name__ == "__main__":
    test_database()
