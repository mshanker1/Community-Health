import pandas as pd
import numpy as np
import sqlite3
from typing import Dict, List, Tuple
import json

class CountyHealthDataProcessor:
    """
    A robust data processor for county health metrics with automatic
    aggregation and percentile calculation
    """
    
    def __init__(self, db_path='county_health_improved.db'):
        self.db_path = db_path
        self.conn = None
        
        # Define the hierarchy and aggregation rules
        self.hierarchy = {
            'society': {
                'health': ['life_expectancy', 'infant_mortality', 'obesity_rate', 'quality_of_life'],
                'wealth': ['median_income', 'home_ownership', 'income_inequality', 'child_poverty'],
                'education': ['preschool_enrollment', 'high_school_graduation', 'college_degree', 'advanced_degree'],
                'community': ['housing_problems', 'food_insecurity', 'internet_access', 'violent_crime'],
                'population': ['working_age_ratio', 'dependency_ratio', 'diversity_index', 'rural_percent']
            },
            'economy': {
                'business': ['gdp_per_capita', 'gdp_growth', 'business_creation', 'patents_per_capita'],
                'government': ['gov_employment_ratio', 'voter_participation', 'public_services_score'],
                'nonprofit': ['nonprofits_per_capita', 'nonprofit_employment', 'charitable_giving'],
                'employment': ['unemployment_rate', 'average_wage', 'wage_growth', 'pay_equality'],
                'energy': ['renewable_percentage', 'energy_efficiency', 'ev_adoption']
            },
            'nature': {
                'planet': ['co2_per_capita', 'air_quality_pm25', 'water_quality', 'biodiversity_index', 'tree_coverage']
            }
        }
        
        # Define which metrics should be inverted (lower is better)
        self.invert_metrics = {
            'infant_mortality', 'obesity_rate', 'child_poverty', 'income_inequality',
            'housing_problems', 'food_insecurity', 'violent_crime', 'unemployment_rate',
            'co2_per_capita', 'air_quality_pm25'
        }
        
    def create_database_schema(self):
        """Create optimized database schema"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Drop existing tables
        cursor.execute("DROP TABLE IF EXISTS raw_metrics")
        cursor.execute("DROP TABLE IF EXISTS metric_metadata")
        cursor.execute("DROP TABLE IF EXISTS aggregated_scores")
        cursor.execute("DROP TABLE IF EXISTS counties")
        
        # Create tables with proper schema
        cursor.execute("""
            CREATE TABLE counties (
                fips INTEGER PRIMARY KEY,
                state TEXT NOT NULL,
                county TEXT NOT NULL,
                state_name TEXT,
                UNIQUE(state, county)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE metric_metadata (
                metric_id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                subcategory TEXT NOT NULL,
                metric TEXT NOT NULL,
                display_name TEXT,
                description TEXT,
                unit TEXT,
                higher_is_better BOOLEAN DEFAULT 1,
                weight REAL DEFAULT 1.0,
                UNIQUE(category, subcategory, metric)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE raw_metrics (
                fips INTEGER,
                metric_id TEXT,
                value REAL,
                year INTEGER DEFAULT 2024,
                PRIMARY KEY (fips, metric_id, year),
                FOREIGN KEY (fips) REFERENCES counties(fips),
                FOREIGN KEY (metric_id) REFERENCES metric_metadata(metric_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE aggregated_scores (
                fips INTEGER,
                level TEXT,  -- 'category', 'subcategory', or 'overall'
                name TEXT,   -- e.g., 'society', 'society_health', 'overall'
                raw_score REAL,
                percentile_score REAL,
                year INTEGER DEFAULT 2024,
                PRIMARY KEY (fips, level, name, year),
                FOREIGN KEY (fips) REFERENCES counties(fips)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX idx_raw_metrics_fips ON raw_metrics(fips)")
        cursor.execute("CREATE INDEX idx_raw_metrics_metric ON raw_metrics(metric_id)")
        cursor.execute("CREATE INDEX idx_aggregated_fips ON aggregated_scores(fips)")
        cursor.execute("CREATE INDEX idx_aggregated_level ON aggregated_scores(level)")
        
        self.conn.commit()
        
    def import_from_wide_format(self, csv_path: str):
        """Import data from wide format CSV (like your current structure)"""
        df = pd.read_csv(csv_path)
        
        # First, populate counties table
        counties_df = df[['FIPS', 'State', 'County']].drop_duplicates()
        counties_df.columns = ['fips', 'state', 'county']
        counties_df['state_name'] = counties_df['state']  # You can map to full names if needed
        counties_df.to_sql('counties', self.conn, if_exists='append', index=False)
        
        # Parse column names and create metric metadata
        metric_metadata = []
        
        for col in df.columns:
            if col not in ['FIPS', 'State', 'County']:
                parts = col.split('_')
                if len(parts) >= 2:
                    category = parts[0].lower()
                    subcategory = parts[1].lower()
                    
                    # Handle special cases
                    if subcategory == 'non-profit':
                        subcategory = 'nonprofit'
                    
                    # Extract metric name
                    metric_parts = parts[2:] if len(parts) > 2 else [subcategory]
                    metric = '_'.join(metric_parts).lower()
                    
                    # Clean up metric names
                    metric = (metric.replace('keyindicator', '')
                                   .replace('(', '_')
                                   .replace(')', '')
                                   .replace(',', '')
                                   .replace('-', '_')
                                   .strip('_'))
                    
                    metric_id = f"{category}_{subcategory}_{metric}"
                    
                    metadata = {
                        'metric_id': metric_id,
                        'category': category,
                        'subcategory': subcategory,
                        'metric': metric,
                        'display_name': ' '.join(parts[2:]) if len(parts) > 2 else subcategory.title(),
                        'description': f"{category.title()} - {subcategory.title()} - {metric.replace('_', ' ').title()}",
                        'unit': 'score',  # Default, can be updated
                        'higher_is_better': 1 if metric not in self.invert_metrics else 0,
                        'weight': 1.0
                    }
                    
                    metric_metadata.append(metadata)
        
        # Insert metric metadata
        metadata_df = pd.DataFrame(metric_metadata).drop_duplicates(subset=['metric_id'])
        metadata_df.to_sql('metric_metadata', self.conn, if_exists='append', index=False)
        
        # Convert to long format and insert raw metrics
        raw_metrics = []
        
        for _, row in df.iterrows():
            fips = row['FIPS']
            
            for col in df.columns:
                if col not in ['FIPS', 'State', 'County']:
                    parts = col.split('_')
                    if len(parts) >= 2:
                        category = parts[0].lower()
                        subcategory = parts[1].lower()
                        
                        if subcategory == 'non-profit':
                            subcategory = 'nonprofit'
                        
                        metric_parts = parts[2:] if len(parts) > 2 else [subcategory]
                        metric = '_'.join(metric_parts).lower()
                        metric = (metric.replace('keyindicator', '')
                                       .replace('(', '_')
                                       .replace(')', '')
                                       .replace(',', '')
                                       .replace('-', '_')
                                       .strip('_'))
                        
                        metric_id = f"{category}_{subcategory}_{metric}"
                        value = row[col]
                        
                        if pd.notna(value) and value != '':
                            try:
                                numeric_value = float(value)
                                raw_metrics.append({
                                    'fips': int(fips),
                                    'metric_id': metric_id,
                                    'value': numeric_value,
                                    'year': 2024
                                })
                            except:
                                pass
        
        # Insert raw metrics
        metrics_df = pd.DataFrame(raw_metrics)
        metrics_df.to_sql('raw_metrics', self.conn, if_exists='append', index=False)
        
        self.conn.commit()
        print(f"Imported {len(raw_metrics)} metrics from {len(counties_df)} counties")
        
    def calculate_percentiles(self):
        """Calculate percentile ranks for all metrics"""
        cursor = self.conn.cursor()
        
        # Get all unique metrics
        metrics = pd.read_sql("""
            SELECT DISTINCT m.metric_id, m.higher_is_better 
            FROM metric_metadata m
            JOIN raw_metrics r ON m.metric_id = r.metric_id
        """, self.conn)
        
        for _, metric_row in metrics.iterrows():
            metric_id = metric_row['metric_id']
            higher_is_better = metric_row['higher_is_better']
            
            # Get all values for this metric
            values_df = pd.read_sql(f"""
                SELECT fips, value 
                FROM raw_metrics 
                WHERE metric_id = '{metric_id}'
                ORDER BY value
            """, self.conn)
            
            if len(values_df) > 0:
                # Calculate percentile ranks
                if higher_is_better:
                    values_df['percentile'] = values_df['value'].rank(pct=True) * 100
                else:
                    values_df['percentile'] = (1 - values_df['value'].rank(pct=True)) * 100
                
                # Update the raw_metrics table with percentiles
                for _, row in values_df.iterrows():
                    cursor.execute("""
                        UPDATE raw_metrics 
                        SET value = ? 
                        WHERE fips = ? AND metric_id = ?
                    """, (row['percentile'], row['fips'], metric_id))
        
        self.conn.commit()
        
    def calculate_aggregated_scores(self):
        """Calculate aggregated scores at subcategory and category levels"""
        
        # Calculate subcategory scores
        subcategory_scores = pd.read_sql("""
            SELECT 
                r.fips,
                m.category,
                m.subcategory,
                AVG(r.value) as avg_score
            FROM raw_metrics r
            JOIN metric_metadata m ON r.metric_id = m.metric_id
            GROUP BY r.fips, m.category, m.subcategory
        """, self.conn)
        
        # Insert subcategory scores
        for _, row in subcategory_scores.iterrows():
            self.conn.execute("""
                INSERT OR REPLACE INTO aggregated_scores (fips, level, name, raw_score, year)
                VALUES (?, 'subcategory', ?, ?, 2024)
            """, (row['fips'], f"{row['category']}_{row['subcategory']}", row['avg_score']))
        
        # Calculate category scores
        category_scores = pd.read_sql("""
            SELECT 
                fips,
                SUBSTR(name, 1, INSTR(name, '_') - 1) as category,
                AVG(raw_score) as avg_score
            FROM aggregated_scores
            WHERE level = 'subcategory'
            GROUP BY fips, category
        """, self.conn)
        
        # Insert category scores
        for _, row in category_scores.iterrows():
            self.conn.execute("""
                INSERT OR REPLACE INTO aggregated_scores (fips, level, name, raw_score, year)
                VALUES (?, 'category', ?, ?, 2024)
            """, (row['fips'], row['category'], row['avg_score']))
        
        # Calculate overall scores
        overall_scores = pd.read_sql("""
            SELECT 
                fips,
                AVG(raw_score) as avg_score
            FROM aggregated_scores
            WHERE level = 'category'
            GROUP BY fips
        """, self.conn)
        
        # Insert overall scores
        for _, row in overall_scores.iterrows():
            self.conn.execute("""
                INSERT OR REPLACE INTO aggregated_scores (fips, level, name, raw_score, year)
                VALUES (?, 'overall', 'overall', ?, 2024)
            """, (row['fips'], row['avg_score']))
        
        # Calculate percentiles for aggregated scores
        for level in ['subcategory', 'category', 'overall']:
            scores_df = pd.read_sql(f"""
                SELECT fips, name, raw_score
                FROM aggregated_scores
                WHERE level = '{level}'
            """, self.conn)
            
            for name in scores_df['name'].unique():
                name_df = scores_df[scores_df['name'] == name].copy()
                name_df['percentile'] = name_df['raw_score'].rank(pct=True) * 100
                
                for _, row in name_df.iterrows():
                    self.conn.execute("""
                        UPDATE aggregated_scores
                        SET percentile_score = ?
                        WHERE fips = ? AND level = ? AND name = ?
                    """, (row['percentile'], row['fips'], level, name))
        
        self.conn.commit()
        
    def get_county_data_for_dashboard(self, fips: int) -> Dict:
        """Get structured data for the dashboard"""
        
        # Get aggregated scores
        scores_df = pd.read_sql("""
            SELECT level, name, percentile_score
            FROM aggregated_scores
            WHERE fips = ? AND level = 'subcategory'
        """, self.conn, params=[fips])
        
        # Structure for dashboard
        structured_data = {
            'society': {},
            'economy': {},
            'nature': {}
        }
        
        for _, row in scores_df.iterrows():
            parts = row['name'].split('_')
            if len(parts) == 2:
                category, subcategory = parts
                if category in structured_data:
                    structured_data[category][subcategory.upper()] = row['percentile_score']
        
        return structured_data
    
    def export_summary_report(self, output_path='county_health_summary.csv'):
        """Export a summary report with all scores"""
        
        summary_df = pd.read_sql("""
            SELECT 
                c.fips,
                c.state,
                c.county,
                a.level,
                a.name,
                a.raw_score,
                a.percentile_score
            FROM counties c
            JOIN aggregated_scores a ON c.fips = a.fips
            ORDER BY c.state, c.county, a.level, a.name
        """, self.conn)
        
        summary_df.to_csv(output_path, index=False)
        print(f"Summary report exported to {output_path}")

# Example usage
if __name__ == "__main__":
    # Initialize processor
    processor = CountyHealthDataProcessor()
    
    # Create database schema
    processor.create_database_schema()
    
    # Import your existing CSV
    processor.import_from_wide_format('RVN3.csv')
    
    # Calculate percentiles
    processor.calculate_percentiles()
    
    # Calculate aggregated scores
    processor.calculate_aggregated_scores()
    
    # Export summary
    processor.export_summary_report()
    
    # Test getting data for a county
    test_data = processor.get_county_data_for_dashboard(1001)
    print("\nSample county data:")
    print(json.dumps(test_data, indent=2))
    
    processor.conn.close()
