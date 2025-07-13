import pandas as pd
import numpy as np
import sqlite3
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import re
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MetricDefinition:
    """Defines the structure of a metric"""
    top_level: str
    sub_category: str
    metric_name: str
    full_name: str
    data_type: str = "numeric"
    requires_calculation: bool = False
    weight: float = 1.0

class FlexibleMetricHierarchy:
    """Dynamically builds metric hierarchy from actual data columns"""
    
    def __init__(self, data_columns: List[str]):
        self.data_columns = data_columns
        self.metrics = self._build_from_columns()
        self.hierarchy = self._build_hierarchy()
    
    def _build_from_columns(self) -> Dict[str, MetricDefinition]:
        """Build metric definitions from actual column names"""
        metrics = {}
        
        # Skip the first 3 columns (FIPS, State, County)
        metric_columns = [col for col in self.data_columns if col not in ['FIPS', 'State', 'County', 'county_fips', 'county_name', 'state_code', 'state_name', 'state_fips']]
        
        for col in metric_columns:
            # Parse the column name to extract hierarchy
            parts = col.split('_')
            
            if len(parts) >= 2:
                top_level = parts[0].upper()  # Society, Economy, Nature
                sub_category = parts[1].upper()  # HEALTH, WEALTH, etc.
                
                # Determine if this is an index metric (no third part or same as sub_category)
                if len(parts) == 2 or parts[2].upper() == sub_category:
                    # This is an index metric
                    metric_name = f"{sub_category}_INDEX"
                    requires_calc = True
                else:
                    # This is a component metric
                    metric_name = '_'.join(parts[2:])
                    requires_calc = False
                
                metrics[col] = MetricDefinition(
                    top_level=top_level,
                    sub_category=sub_category,
                    metric_name=metric_name,
                    full_name=col,
                    requires_calculation=requires_calc
                )
                
                logger.debug(f"Mapped column '{col}' -> {top_level}.{sub_category}.{metric_name}")
        
        logger.info(f"Built hierarchy for {len(metrics)} metrics")
        return metrics
    
    def _build_hierarchy(self) -> Dict[str, Dict[str, List[str]]]:
        """Build hierarchical structure from metrics"""
        hierarchy = {}
        
        for metric_key, metric_def in self.metrics.items():
            if metric_def.top_level not in hierarchy:
                hierarchy[metric_def.top_level] = {}
            
            if metric_def.sub_category not in hierarchy[metric_def.top_level]:
                hierarchy[metric_def.top_level][metric_def.sub_category] = []
            
            hierarchy[metric_def.top_level][metric_def.sub_category].append(metric_key)
        
        return hierarchy
    
    def get_sub_metrics(self, top_level: str, sub_category: str) -> List[str]:
        """Get all metrics for a specific sub-category"""
        return self.hierarchy.get(top_level, {}).get(sub_category, [])
    
    def is_index_metric(self, metric_name: str) -> bool:
        """Check if a metric is an index that needs calculation"""
        return self.metrics.get(metric_name, MetricDefinition("", "", "", "")).requires_calculation

class SimpleDataProcessor:
    """Simplified data processor that works with any column structure"""
    
    def __init__(self):
        pass
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize data"""
        logger.info(f"Starting data cleaning with {len(df)} rows")
        
        # Create standardized column names
        df = df.rename(columns={
            'FIPS': 'county_fips',
            'State': 'state_name', 
            'County': 'county_name'
        })
        
        # Remove rows with null values in essential columns
        initial_count = len(df)
        df = df.dropna(subset=['county_fips', 'state_name', 'county_name'])
        if len(df) < initial_count:
            logger.info(f"Removed {initial_count - len(df)} rows with missing FIPS/State/County data")
        
        # Standardize county FIPS codes
        df['county_fips'] = df['county_fips'].astype(str).str.replace('.0', '').str.zfill(5)
        
        # Create state codes
        state_mapping = {
            'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
            'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
            'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
            'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
            'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
            'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
            'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
            'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
            'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
            'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
            'District of Columbia': 'DC', 'Puerto Rico': 'PR'
        }
        
        df['state_code'] = df['state_name'].map(state_mapping)
        mask = df['state_code'].isna()
        df.loc[mask, 'state_code'] = df.loc[mask, 'state_name'].str.upper().str.strip()
        df['state_code'] = df['state_code'].fillna('XX')
        
        # Clean county names
        df['county_name'] = df['county_name'].astype(str).str.replace(r'\s+County\s*$', '', regex=True).str.strip().str.title()
        df['county_name'] = df['county_name'].fillna('Unknown County')
        
        logger.info(f"Data cleaned: {len(df)} rows remaining")
        return df
    
    def calculate_simple_indices(self, df: pd.DataFrame, hierarchy: FlexibleMetricHierarchy) -> pd.DataFrame:
        """Calculate index metrics using simple averaging"""
        result_df = df.copy()
        
        for top_level, sub_categories in hierarchy.hierarchy.items():
            for sub_category, metrics in sub_categories.items():
                
                # Find index and component metrics
                index_metrics = [m for m in metrics if hierarchy.is_index_metric(m)]
                component_metrics = [m for m in metrics if not hierarchy.is_index_metric(m)]
                
                # Calculate index from existing component metrics
                if component_metrics:
                    existing_components = [m for m in component_metrics if m in result_df.columns]
                    
                    if existing_components and len(existing_components) > 0:
                        try:
                            # Simple average of existing components
                            component_data = result_df[existing_components]
                            
                            # Create index name if it doesn't exist
                            index_name = f"{top_level}_{sub_category}"
                            
                            if index_name in result_df.columns:
                                # If index already exists and has values, keep it
                                if result_df[index_name].notna().any():
                                    logger.info(f"Index {index_name} already exists with values, keeping original")
                                    continue
                            
                            # Calculate new index
                            result_df[index_name] = component_data.mean(axis=1)
                            logger.info(f"Calculated {index_name} from {len(existing_components)} components: {existing_components}")
                            
                        except Exception as e:
                            logger.warning(f"Could not calculate index for {top_level}_{sub_category}: {str(e)}")
        
        return result_df

class SimpleETL:
    """Simplified ETL that works with your exact data structure"""
    
    def __init__(self, db_path: str = "county_health.db"):
        self.db_path = db_path
        self.processor = SimpleDataProcessor()
        self.setup_database()
    
    def setup_database(self):
        """Create database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS raw_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                county_fips TEXT NOT NULL,
                county_name TEXT NOT NULL,
                state_code TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                data_year INTEGER NOT NULL,
                data_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS computed_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                county_fips TEXT NOT NULL,
                county_name TEXT NOT NULL,
                state_code TEXT NOT NULL,
                top_level TEXT NOT NULL,
                sub_category TEXT,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                percentile_rank REAL,
                data_year INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS counties (
                fips_code TEXT PRIMARY KEY,
                county_name TEXT NOT NULL,
                state_code TEXT NOT NULL,
                state_name TEXT NOT NULL,
                population INTEGER,
                rural_percentage REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def run_pipeline(self, file_path: str, data_year: int, data_source: str):
        """Run the complete ETL pipeline"""
        logger.info(f"Starting simple ETL pipeline for {file_path}")
        
        try:
            # Load data
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
            
            logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
            
            # Build hierarchy from actual columns
            hierarchy = FlexibleMetricHierarchy(df.columns.tolist())
            
            # Clean data
            cleaned_df = self.processor.clean_data(df)
            
            # Calculate indices (optional - only if you want computed indices)
            # final_df = self.processor.calculate_simple_indices(cleaned_df, hierarchy)
            final_df = cleaned_df  # Skip index calculation for now
            
            # Load to database
            self.load_data(final_df, data_year, data_source, hierarchy)
            
            logger.info("ETL pipeline completed successfully!")
            return final_df
            
        except Exception as e:
            logger.error(f"ETL pipeline failed: {str(e)}")
            raise
    
    def load_data(self, df: pd.DataFrame, data_year: int, data_source: str, hierarchy: FlexibleMetricHierarchy):
        """Load data to database"""
        conn = sqlite3.connect(self.db_path)
        
        # Load county metadata
        county_df = df[['county_fips', 'county_name', 'state_code', 'state_name']].drop_duplicates()
        county_df = county_df.rename(columns={'county_fips': 'fips_code'})
        county_df.to_sql('counties', conn, if_exists='replace', index=False)
        logger.info(f"Loaded {len(county_df)} county records")
        
        # Load metrics in long format
        metadata_cols = ['county_fips', 'county_name', 'state_code', 'state_name']
        metric_cols = [col for col in df.columns if col not in metadata_cols]
        
        long_df = df.melt(
            id_vars=['county_fips', 'county_name', 'state_code'],
            value_vars=metric_cols,
            var_name='metric_name',
            value_name='metric_value'
        )
        
        long_df['data_year'] = data_year
        long_df['data_source'] = data_source
        long_df = long_df.dropna(subset=['metric_value'])
        
        long_df.to_sql('raw_metrics', conn, if_exists='append', index=False)
        logger.info(f"Loaded {len(long_df)} raw metric records")
        
        # Create computed metrics with percentiles
        records = []
        for metric_col in metric_cols:
            if metric_col in df.columns:
                metric_data = df[['county_fips', 'county_name', 'state_code', metric_col]].dropna()
                
                if len(metric_data) > 0:
                    # Calculate percentiles
                    percentiles = metric_data[metric_col].rank(pct=True) * 100
                    
                    # Get hierarchy info
                    metric_def = hierarchy.metrics.get(metric_col)
                    if metric_def:
                        top_level = metric_def.top_level
                        sub_category = metric_def.sub_category
                        metric_name = metric_def.metric_name
                    else:
                        # Fallback parsing
                        parts = metric_col.split('_')
                        top_level = parts[0] if len(parts) > 0 else 'OTHER'
                        sub_category = parts[1] if len(parts) > 1 else 'OTHER'
                        metric_name = metric_col
                    
                    for idx, row in metric_data.iterrows():
                        records.append({
                            'county_fips': row['county_fips'],
                            'county_name': row['county_name'],
                            'state_code': row['state_code'],
                            'top_level': top_level,
                            'sub_category': sub_category,
                            'metric_name': metric_name,
                            'metric_value': row[metric_col],
                            'percentile_rank': percentiles.loc[idx],
                            'data_year': data_year
                        })
        
        if records:
            computed_df = pd.DataFrame(records)
            computed_df.to_sql('computed_metrics', conn, if_exists='append', index=False)
            logger.info(f"Loaded {len(computed_df)} computed metric records")
        
        conn.close()

# Usage
if __name__ == "__main__":
    etl = SimpleETL()
    
    try:
        result_df = etl.run_pipeline("Revised-Sheet3.csv", 2023, "County Health Data")
        print(f"✅ SUCCESS: Processed {len(result_df)} counties")
        print(f"📊 Columns processed: {len(result_df.columns)}")
        print(f"🏛️ Sample counties: {result_df['county_name'].head().tolist()}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()