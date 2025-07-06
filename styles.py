"""
CSS styling for the dashboard
"""

def get_custom_css():
    """Return the custom CSS styling for the dashboard"""
    return '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .header {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 10px;
            }
            .header-title { margin: 0; font-size: 2.5em; }
            .header-subtitle { margin: 5px 0 0 0; opacity: 0.9; }
            
            .breadcrumb {
                margin-top: 10px;
                font-size: 0.9em;
                opacity: 0.8;
            }
            .breadcrumb-item { color: white; }
            .breadcrumb-item.active { font-weight: bold; }
            .breadcrumb-separator { margin: 0 5px; }
            
            .control-panel {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
            }
            .control-item { display: flex; flex-direction: column; }
            .control-label { font-weight: bold; margin-bottom: 5px; color: #333; }
            
            .instruction-text {
                color: #666;
                font-style: italic;
                margin-bottom: 15px;
            }
            
            .charts-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 30px;
            }
            .chart-container { 
                background: white; 
                border-radius: 10px; 
                padding: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .section-title { 
                margin-top: 0; 
                color: #333; 
                font-size: 1.5em;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            
            .section-subtitle {
                margin: 20px 0 10px 0;
                color: #555;
                font-size: 1.2em;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            .stat-card {
                text-align: center;
                padding: 15px;
                border-radius: 8px;
                border: 2px solid #ddd;
                background: white;
            }
            .stat-card.health { border-color: #FF6B6B; }
            .stat-card.wealth { border-color: #4ECDC4; }
            .stat-card.education { border-color: #45B7D1; }
            .stat-card.community { border-color: #FFA07A; }
            .stat-card.sub-metric { border-color: #9B59B6; }
            
            .stat-value { margin: 0; font-size: 1.8em; font-weight: bold; color: #333; }
            .stat-label { margin: 5px 0 0 0; color: #666; font-size: 0.9em; }
            
            .comparison-text {
                margin: 5px 0 0 0;
                font-size: 0.8em;
                font-weight: bold;
            }
            .comparison-text.positive { color: #28a745; }
            .comparison-text.negative { color: #dc3545; }
            .comparison-text.neutral { color: #6c757d; }
            
            .insights-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            .insight-card {
                text-align: center;
                padding: 15px;
                border-radius: 8px;
                background: #f8f9fa;
                border: 1px solid #ddd;
            }
            .insight-value { 
                margin: 0; 
                font-size: 1.6em; 
                font-weight: bold; 
                color: #667eea; 
            }
            .insight-label { 
                margin: 5px 0 0 0; 
                color: #666; 
                font-size: 0.85em; 
            }
            
            .insights-section {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 30px;
                border-left: 5px solid #667eea;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            
            .charts-section {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }
            
            .context-panel {
                margin-top: 20px;
                padding: 15px;
                background: #f1f3f4;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            .context-text {
                margin: 5px 0;
                color: #555;
                font-size: 0.9em;
            }
            
            .nav-btn, .reset-btn {
                padding: 8px 16px;
                margin: 5px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
            }
            .nav-btn {
                background: #667eea;
                color: white;
            }
            .nav-btn:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            .reset-btn {
                background: #dc3545;
                color: white;
            }
            .nav-btn:hover:not(:disabled), .reset-btn:hover {
                opacity: 0.8;
            }
            
            @media (max-width: 768px) {
                .charts-row { grid-template-columns: 1fr; }
                .control-panel { grid-template-columns: 1fr; }
                .stats-grid { grid-template-columns: repeat(2, 1fr); }
                .insights-grid { grid-template-columns: repeat(2, 1fr); }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''