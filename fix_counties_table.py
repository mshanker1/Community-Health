import sqlite3
import pandas as pd

def fix_counties_table(db_file='county_health.db'):
    """Fix the counties table that has NULL values"""
    
    print(f"Fixing counties table in {db_file}...")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Drop the broken counties table
        print("Dropping old counties table...")
        cursor.execute("DROP TABLE IF EXISTS counties")
        
        # Recreate it properly
        print("Creating new counties table...")
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
        
        # Create index
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_counties_fips ON counties(fips_code)")
        
        # Verify the fix
        print("\nVerifying the fix...")
        sample_data = pd.read_sql("SELECT * FROM counties LIMIT 10", conn)
        print(f"Sample data from fixed counties table:")
        print(sample_data)
        
        # Count total counties
        count = cursor.execute("SELECT COUNT(*) FROM counties WHERE fips_code IS NOT NULL").fetchone()[0]
        print(f"\nTotal valid counties: {count}")
        
        conn.commit()
        print("\nCounties table fixed successfully!")
        
    except Exception as e:
        print(f"Error fixing counties table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_counties_table()
