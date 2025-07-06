"""
Main application file for the County Well-Being Dashboard
"""
import os
import dash
from dash import dcc, html
from data_loader import load_data
from layouts import create_app_layout
from callbacks import register_callbacks
from styles import get_custom_css

# Initialize the Dash app
app = dash.Dash(__name__, 
                external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'],
                suppress_callback_exceptions=True)

# IMPORTANT: Expose server for Render deployment
server = app.server

# Load data
df = load_data()

# Set up the layout
app.layout = create_app_layout(df)

# Register all callbacks
register_callbacks(app, df)

# Apply custom CSS
app.index_string = get_custom_css()

if __name__ == '__main__':
    # RENDER CONFIGURATION: Use environment port or default to 8050
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run_server(
        host='0.0.0.0',  # Required for Render
        port=port,       # Uses Render's assigned port
        debug=debug      # Disable debug in production
    )