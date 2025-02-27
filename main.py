import os
import subprocess
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, callback_context
from dash.dependencies import Input, Output, State

# Import modularized components
from data_processing import process_txt_files, load_data, transform_data, filter_data
from visualization import create_base_figure
from translations import (
    get_translations, get_tarif_translations, 
    get_kirchensteuer_translations, get_language_region_translations
)

# Global flag to control data recreation
RECREATE_DATA = False  # Set to True to reprocess all TXT files, False to use existing CSV

def create_dash_app(df_filtered):
    # Canton name mapping
    canton_names = {
        'AG': 'Aargau (AG)',
        'AI': 'Appenzell Innerrhoden (AI)',
        'AR': 'Appenzell Ausserrhoden (AR)',
        'BE': 'Bern (BE)',
        'BL': 'Basel-Landschaft (BL)',
        'BS': 'Basel-Stadt (BS)',
        'FR': 'Fribourg (FR)',
        'GE': 'Geneva (GE)',
        'GL': 'Glarus (GL)',
        'GR': 'Graubünden (GR)',
        'JU': 'Jura (JU)',
        'LU': 'Luzern (LU)',
        'NE': 'Neuchâtel (NE)',
        'NW': 'Nidwalden (NW)',
        'OW': 'Obwalden (OW)',
        'SG': 'St. Gallen (SG)',
        'SH': 'Schaffhausen (SH)',
        'SO': 'Solothurn (SO)',
        'SZ': 'Schwyz (SZ)',
        'TG': 'Thurgau (TG)',
        'TI': 'Ticino (TI)',
        'UR': 'Uri (UR)',
        'VD': 'Vaud (VD)',
        'VS': 'Valais (VS)',
        'ZG': 'Zug (ZG)',
        'ZH': 'Zürich (ZH)'
    }
    
    # Language region mapping
    language_regions = {
        'German': ['AG', 'AI', 'AR', 'BE', 'BL', 'BS', 'GL', 'GR', 'LU', 'NW', 'OW', 'SG', 'SH', 'SO', 'SZ', 'TG', 'UR', 'ZG', 'ZH'],
        'French': ['FR', 'GE', 'JU', 'NE', 'VD', 'VS'],
        'Italian': ['TI'],
        'Multilingual': ['BE', 'FR', 'GR', 'VS']  # These cantons appear in multiple regions
    }
    
    # Get translations from the translations module
    translations = get_translations()
    tarif_translations = get_tarif_translations()
    kirchensteuer_translations = get_kirchensteuer_translations()
    language_region_translations = get_language_region_translations()
    
    # Format tarif options with HTML for better display
    formatted_tarif_options = {
        'A': 'A - Tarif für alleinstehende Personen',
        'B': 'B - Tarif für verheiratete Alleinverdiener',
        'C': 'C - Tarif für verheiratete Doppelverdiener',
        'D': 'D - Tarif für Personen, denen Beiträge an die AHV zurückerstattet werden',
        'E': 'E - Tarif für Einkünfte, die im vereinfachten Abrechnungsverfahren besteuert werden',
        'G': 'G - Tarif für Ersatzeinkünfte, die nicht über die Arbeitgeber ausbezahlt werden',
        'H': 'H - Tarif für alleinstehende Personen mit Kindern',
        'L': 'L - Tarif für Grenzgänger aus Deutschland (Tarifcode A)',
        'M': 'M - Tarif für Grenzgänger aus Deutschland (Tarifcode B)',
        'N': 'N - Tarif für Grenzgänger aus Deutschland (Tarifcode C)',
        'P': 'P - Tarif für Grenzgänger aus Deutschland (Tarifcode H)',
        'Q': 'Q - Tarif für Grenzgänger aus Deutschland (Tarifcode G)'
    }

    # Plain text versions for the title
    tarif_options = {
        'A': 'A - Tarif für alleinstehende Personen',
        'B': 'B - Tarif für verheiratete Alleinverdiener',
        'C': 'C - Tarif für verheiratete Doppelverdiener',
        'D': 'D - Tarif für Personen, denen Beiträge an die AHV zurückerstattet werden',
        'E': 'E - Tarif für Einkünfte, die im vereinfachten Abrechnungsverfahren besteuert werden',
        'G': 'G - Tarif für Ersatzeinkünfte, die nicht über die Arbeitgeber ausbezahlt werden',
        'H': 'H - Tarif für alleinstehende Personen mit Kindern',
        'L': 'L - Tarif für Grenzgänger aus Deutschland (Tarifcode A)',
        'M': 'M - Tarif für Grenzgänger aus Deutschland (Tarifcode B)',
        'N': 'N - Tarif für Grenzgänger aus Deutschland (Tarifcode C)',
        'P': 'P - Tarif für Grenzgänger aus Deutschland (Tarifcode H)',
        'Q': 'Q - Tarif für Grenzgänger aus Deutschland (Tarifcode G)'
    }
    
    # Kirchensteuer options
    kirchensteuer_options = {
        'N': 'Without Church Tax',
        'Y': 'With Church Tax'
    }
    
    # Add custom CSS for hover effects
    app = Dash(__name__, 
               external_stylesheets=['https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap'])
    
    # Custom CSS for hover effects
    app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                /* Global left alignment for all dropdown elements */
                .Select-option, 
                .Select-value, 
                .Select-control, 
                .Select-placeholder,
                .Select-input,
                .Select-value-label,
                .VirtualizedSelectOption,
                .VirtualizedSelectFocusedOption,
                .Select-menu-outer div,
                .Select-menu-outer span,
                .Select-menu-outer * {
                    text-align: left !important;
                }
                
                /* Override any potential center alignment */
                #tarif-selector .Select-option,
                #tarif-selector .VirtualizedSelectOption,
                #tarif-selector .VirtualizedSelectFocusedOption,
                #tarif-selector .Select-menu-outer div,
                #tarif-selector .Select-menu-outer span,
                #tarif-selector .Select-menu-outer * {
                    text-align: left !important;
                    display: block !important;
                    margin-left: 0 !important;
                    margin-right: auto !important;
                }
                
                /* Rest of your existing styles */
                .dash-dropdown .Select-control:hover {
                    border-color: #2196F3;
                }
                .dash-dropdown .Select-menu-outer {
                    border-radius: 4px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    width: 400px !important;
                    max-width: 400px !important;
                }
                .dash-dropdown .VirtualizedSelectOption {
                    transition: background-color 0.2s;
                    white-space: normal !important;
                    line-height: 1.4 !important;
                    padding: 8px 12px !important;
                }
                .dash-dropdown .VirtualizedSelectFocusedOption {
                    background-color: rgba(33, 150, 243, 0.1);
                }
                .rc-slider-track {
                    background-color: #2196F3;
                }
                .rc-slider-handle {
                    border-color: #2196F3;
                }
                .rc-slider-handle:hover {
                    border-color: #0b7dda;
                }
                .rc-slider-handle:active {
                    border-color: #0b7dda;
                    box-shadow: 0 0 5px #0b7dda;
                }
                /* Custom styling for tarif dropdown */
                #tarif-selector .Select-menu-outer {
                    width: 550px !important;
                    max-width: 550px !important;
                    left: 0;
                }
                #tarif-selector .Select-option {
                    white-space: normal !important;
                    padding: 12px 16px !important;
                    border-bottom: 1px solid #f0f0f0;
                    font-size: 14px;
                }
                #tarif-selector .VirtualizedSelectOption:hover {
                    background-color: #f5f9ff !important;
                }
                #tarif-selector .VirtualizedSelectFocusedOption {
                    background-color: #e6f2ff !important;
                }
                /* Style for the tarif code letter */
                .tarif-code-letter {
                    font-weight: bold;
                    color: #2196F3;
                    display: inline-block;
                    width: 20px;
                }
                /* Language flag styling */
                .language-flag {
                    width: 30px;
                    height: 20px;
                    cursor: pointer;
                    border: 2px solid transparent;
                    border-radius: 4px;
                    transition: all 0.2s ease;
                    margin: 0 5px;
                }
                .language-flag:hover {
                    transform: scale(1.1);
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                }
                .language-flag.active {
                    border-color: #2196F3;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
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
    
    # Create sorted list of cantons
    cantons = sorted(df_filtered['kanton'].unique())
    
    # Define consistent font style
    font_family = "'Open Sans', Arial, Helvetica, sans-serif"
    font_color = '#666666'  # GREY40
    
    # Minimalist dropdown style
    dropdown_style = {
        'width': '100%',
        'backgroundColor': 'white',
        'fontFamily': font_family,
        'color': font_color,
        'border': '1px solid #e0e0e0',
        'borderRadius': '4px',
        'transition': 'border-color 0.3s'
    }
    
    # Tarif dropdown style with increased height for options
    tarif_dropdown_style = {
        'width': '100%',
        'backgroundColor': 'white',
        'fontFamily': font_family,
        'color': font_color,
        'border': '1px solid #e0e0e0',
        'borderRadius': '4px',
        'transition': 'border-color 0.3s'
    }
    
    # Get min and max income values from the data
    min_income = int(df_filtered['steuerbares_einkommen'].min())
    max_income = int(df_filtered['steuerbares_einkommen'].max())
    
    # Add custom CSS styling
    app.layout = html.Div([
        # Store for current language
        dcc.Store(id='current-language', data='en'),  # Default to English
        
        html.Div([
            # Left column for dropdowns and slider
            html.Div([
                # Language selector
                html.Div([
                    html.Label("Language / Sprache / Langue / Lingua:", 
                        style={
                            'marginBottom': '8px',
                            'fontFamily': font_family,
                            'color': 'black',
                            'display': 'block',
                            'whiteSpace': 'nowrap'
                        }
                    ),
                    html.Div([
                        html.Img(
                            src='/assets/flag-en.png',
                            id='flag-en',
                            className='language-flag active',
                            title='English'
                        ),
                        html.Img(
                            src='/assets/flag-de.png',
                            id='flag-de',
                            className='language-flag',
                            title='Deutsch'
                        ),
                        html.Img(
                            src='/assets/flag-fr.png',
                            id='flag-fr',
                            className='language-flag',
                            title='Français'
                        ),
                        html.Img(
                            src='/assets/flag-it.png',
                            id='flag-it',
                            className='language-flag',
                            title='Italiano'
                        ),
                    ], style={
                        'display': 'flex',
                        'alignItems': 'center',
                        'marginBottom': '20px'
                    })
                ]),
                
                # Income range slider
                html.Div([
                    html.Label(id='income-label', children="Select Income Range (CHF):", 
                        style={
                            'marginBottom': '8px',
                            'fontFamily': font_family,
                            'color': 'black',
                            'display': 'block',
                            'whiteSpace': 'nowrap'
                        }
                    ),
                    dcc.RangeSlider(
                        id='income-slider',
                        min=min_income,
                        max=max_income,
                        step=500,
                        marks={
                            min_income: f'{min_income:,}',
                            max_income: f'{max_income:,}'
                        },
                        value=[2000, 10000],  # Default to 2000-10000 range
                        allowCross=False,
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], style={'marginBottom': '25px'}),
                
                # Tarif code dropdown
                html.Div([
                    html.Label(id='tarif-label', children="Select Tarif Code:", 
                        style={
                            'marginBottom': '8px',
                            'fontFamily': font_family,
                            'color': 'black',
                            'display': 'block',
                            'whiteSpace': 'nowrap'
                        }
                    ),
                    dcc.Dropdown(
                        id='tarif-selector',
                        options=[
                            {'label': value, 'value': key} 
                            for key, value in formatted_tarif_options.items()
                        ],
                        value='A',  # Default to tarif A
                        placeholder="Select tarif code...",
                        style=tarif_dropdown_style,
                        optionHeight=35,  # Further increase option height
                        clearable=False
                    )
                ], style={'marginBottom': '20px'}),
                
                # Kirchensteuer dropdown
                html.Div([
                    html.Label(id='church-label', children="Church Tax Option:", 
                        style={
                            'marginBottom': '8px',
                            'fontFamily': font_family,
                            'color': 'black',
                            'display': 'block',
                            'whiteSpace': 'nowrap'
                        }
                    ),
                    dcc.Dropdown(
                        id='kirchensteuer-selector',
                        options=[
                            {'label': value, 'value': key} 
                            for key, value in kirchensteuer_options.items()
                        ],
                        value='N',  # Default to without church tax
                        placeholder="Select church tax option...",
                        style=dropdown_style,
                    )
                ], style={'marginBottom': '20px'}),
                
                # Children dropdown
                html.Div([
                    html.Label(id='children-label', children="Number of Children:", 
                        style={
                            'marginBottom': '8px',
                            'fontFamily': font_family,
                            'color': 'black',
                            'display': 'block',
                            'whiteSpace': 'nowrap'
                        }
                    ),
                    dcc.Dropdown(
                        id='children-selector',
                        options=[
                            {'label': f"{i} {'Child' if i == 1 else 'Children'}", 'value': i} 
                            for i in sorted(df_filtered['anzahl_kinder'].unique())
                        ],
                        value=0,  # Default to 0 children
                        placeholder="Select number of children...",
                        style=dropdown_style,
                    )
                ], style={'marginBottom': '20px'}),
                
                # Language region dropdown
                html.Div([
                    html.Label(id='region-label', children="Select Language Region:", 
                        style={
                            'marginBottom': '8px',
                            'fontFamily': font_family,
                            'color': 'black',
                            'display': 'block',
                            'whiteSpace': 'nowrap'
                        }
                    ),
                    dcc.Dropdown(
                        id='region-selector',
                        options=[
                            {'label': region, 'value': region} 
                            for region in language_regions.keys()
                        ],
                        placeholder="Select language region...",
                        style=dropdown_style,
                    )
                ], style={'marginBottom': '20px'}),
                
                # Canton selector dropdown
                html.Div([
                    html.Label(id='canton-label', children="Select Cantons:", 
                        style={
                            'marginBottom': '8px',
                            'fontFamily': font_family,
                            'color': 'black',
                            'display': 'block',
                            'whiteSpace': 'nowrap'
                        }
                    ),
                    dcc.Dropdown(
                        id='canton-selector',
                        options=[
                            {'label': canton_names.get(canton, canton), 'value': canton} 
                            for canton in cantons
                        ],
                        multi=True,
                        placeholder="Select cantons...",
                        style=dropdown_style,
                        optionHeight=35,
                        maxHeight=200,  # Reduced from 600 to 300 pixels
                    )
                ])
            ], style={
                'width': '320px',
                'padding': '20px',
                'boxSizing': 'border-box',
                'backgroundColor': 'white',
                'position': 'relative',
                'boxShadow': '2px 2px 8px 8px rgba(200, 200, 200, 0.5)',
                'border': '1px solid #e0e0e0',
                'borderRadius': '4px'
            }),
            
            # Right column for the plot
            html.Div([
                dcc.Graph(
                    id='canton-plot',
                    figure=create_base_figure(df_filtered, canton_names),
                    style={
                        'height': '100%',  # Fill the height of the container
                        'width': '100%'    # Fill the width of the container
                    },
                    config={
                        'displayModeBar': True,  # Always show the modebar instead of on hover
                        'toImageButtonOptions': {
                            'format': 'png',
                            'filename': 'source_tax_visualization',
                            'height': 800,
                            'width': 1200,
                            'scale': 2  # Higher resolution
                        }
                    }
                )
            ], style={
                'flex': '1',
                'paddingLeft': '10px',
                'boxSizing': 'border-box',
                'height': '100%',  # Make sure the container takes full height
                'position': 'relative',  # For positioning the shadow
                'backgroundColor': 'white',
                'boxShadow': '2px 2px 8px 8px rgba(200, 200, 200, 0.5)',  # Light grey shadow with offset
                'border': '1px solid #e0e0e0',
                'borderRadius': '4px'
            })
        ], style={
            'display': 'flex',
            'flexDirection': 'row',
            'width': 'calc(100% - 4cm)',  # 2cm margin on left and right
            'height': 'calc(100vh - 4cm)', # 2cm margin on top and bottom
            'margin': '2cm',              # 2cm margin on all sides
            'boxSizing': 'border-box',
            'gap': '20px'  # Add space between the two columns
        })
    ], style={
        'width': '100%',
        'height': '100vh',
        'fontFamily': font_family,
        'display': 'flex',
        'padding': '0',
        'margin': '0'
    })
    
    # Callback to update language when a flag is clicked
    @app.callback(
        Output('current-language', 'data'),
        [Input('flag-en', 'n_clicks'),
         Input('flag-de', 'n_clicks'),
         Input('flag-fr', 'n_clicks'),
         Input('flag-it', 'n_clicks')],
        [State('current-language', 'data')]
    )
    def update_language(en_clicks, de_clicks, fr_clicks, it_clicks, current_lang):
        ctx = callback_context
        if not ctx.triggered:
            return current_lang
            
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'flag-en':
            return 'en'
        elif button_id == 'flag-de':
            return 'de'
        elif button_id == 'flag-fr':
            return 'fr'
        elif button_id == 'flag-it':
            return 'it'
        
        return current_lang
    
    # Callback to update flag styling based on selected language
    @app.callback(
        [Output('flag-en', 'className'),
         Output('flag-de', 'className'),
         Output('flag-fr', 'className'),
         Output('flag-it', 'className')],
        [Input('current-language', 'data')]
    )
    def update_flag_styling(language):
        base_class = 'language-flag'
        active_class = 'language-flag active'
        
        return [
            active_class if language == 'en' else base_class,
            active_class if language == 'de' else base_class,
            active_class if language == 'fr' else base_class,
            active_class if language == 'it' else base_class
        ]
    
    # Callback to update UI labels based on selected language
    @app.callback(
        [Output('income-label', 'children'),
         Output('tarif-label', 'children'),
         Output('church-label', 'children'),
         Output('children-label', 'children'),
         Output('region-label', 'children'),
         Output('canton-label', 'children')],
        [Input('current-language', 'data')]
    )
    def update_ui_labels(language):
        return [
            translations[language]['income_range'],
            translations[language]['tarif_code'],
            translations[language]['church_tax'],
            translations[language]['number_of_children'],
            translations[language]['language_region'],
            translations[language]['select_cantons']
        ]
    
    # Callback to update dropdown options based on selected language
    @app.callback(
        [Output('tarif-selector', 'options'),
         Output('kirchensteuer-selector', 'options'),
         Output('region-selector', 'options')],
        [Input('current-language', 'data')]
    )
    def update_dropdown_options(language):
        # Update tarif options
        tarif_options = [
            {'label': tarif_translations[language][key], 'value': key} 
            for key in tarif_translations[language].keys()
        ]
        
        # Update kirchensteuer options
        kirchensteuer_opts = [
            {'label': kirchensteuer_translations[language][key], 'value': key} 
            for key in kirchensteuer_translations[language].keys()
        ]
        
        # Update language region options
        region_options = [
            {'label': language_region_translations[language][region], 'value': region} 
            for region in language_regions.keys()
        ]
        
        return tarif_options, kirchensteuer_opts, region_options
    
    @app.callback(
        Output('canton-selector', 'value'),
        Input('region-selector', 'value')
    )
    def update_canton_selection(selected_region):
        if not selected_region:
            return []
        
        # Return list of cantons in the selected language region
        return language_regions.get(selected_region, [])
    
    @app.callback(
        Output('canton-plot', 'figure'),
        [Input('canton-selector', 'value'),
         Input('region-selector', 'value'),
         Input('income-slider', 'value'),
         Input('kirchensteuer-selector', 'value'),
         Input('tarif-selector', 'value'),
         Input('children-selector', 'value'),
         Input('current-language', 'data')]
    )
    def update_figure(selected_cantons, selected_region, income_range, kirchensteuer, tarif_code, children, language):
        # Unpack the income range
        x_min, x_max = income_range
        
        # Filter data based on kirchensteuer, tarif code, and children selection
        df_filtered_view = df_filtered[
            (df_filtered['kirchensteuer'] == kirchensteuer) & 
            (df_filtered['tarif_code'] == tarif_code) &
            (df_filtered['anzahl_kinder'] == children)
        ]
        
        # Check if the filtered data is empty
        if df_filtered_view.empty:
            # Create an empty figure with a message
            fig = go.Figure()
            fig.update_layout(
                title=dict(
                    text=translations[language]['no_data_available'],
                    x=0.5,
                    font=dict(size=18, color='#666666', family=font_family)
                ),
                xaxis=dict(
                    title=dict(
                        text=translations[language]['monthly_income'],
                        font=dict(size=12, color='#666666', family=font_family, weight='bold')
                    ),
                    # Let the base figure handle the ticks to ensure grid alignment
                    showgrid=False
                ),
                yaxis=dict(
                    title=dict(
                        text=translations[language]['tax_rate'],
                        font=dict(size=12, color='#666666', family=font_family, weight='bold')
                    ),
                    # Remove ticksuffix since we're adding % in the base figure
                    ticksuffix=''
                )
            )
            return fig
        
        # Get translations for the selected language
        translations = get_translations()[language]
        
        # Pass translations to create_base_figure
        fig = create_base_figure(
            df_filtered_view, 
            canton_names, 
            income_range[0], 
            income_range[1], 
            tarif_code, 
            kirchensteuer, 
            children,
            translations
        )
        
        # Get the church tax label for the title
        church_tax_label = kirchensteuer_translations[language].get(kirchensteuer, '')
        
        # Get the tarif code description for the title
        tarif_label = tarif_translations[language].get(tarif_code, '').split(' - ')[1] if ' - ' in tarif_translations[language].get(tarif_code, '') else tarif_translations[language].get(tarif_code, '')
        
        # Update the title to include all parameters and use the correct language
        fig.update_layout(
            title=dict(
                text=f"{translations['source_tax_progression']}",
                x=0.5,
                font=dict(size=18, color='black', family=font_family, weight='bold')  # Changed to black and bold
            ),
            xaxis=dict(
                title=dict(
                    text=translations['monthly_income'],
                    font=dict(size=12, color='black', family=font_family, weight='bold')  # Changed to black
                ),
                # Let the base figure handle the ticks to ensure grid alignment
                showgrid=False
            ),
            yaxis=dict(
                title=dict(
                    text=translations['tax_rate'],
                    font=dict(size=12, color='black', family=font_family, weight='bold')  # Changed to black
                ),
                # Remove ticksuffix since we're adding % in the base figure
                ticksuffix=''
            )
        )
        
        # Get the indices of selected cantons
        cantons = sorted(df_filtered_view['kanton'].unique())
        canton_to_idx = {canton: idx for idx, canton in enumerate(cantons)}
        
        # Color scale for highlighted cantons
        COLOR_SCALE = [
            '#9A5CB4', '#3F8EFC', '#906C33', '#7B3A96', '#5D5D5D', 
            '#3E8E75', '#5EFF5E', '#F0E68C', '#888888', '#4CA64C', 
            '#A0522D', '#DDA0DD', '#FF00FF', '#000080', '#FFA500', 
            '#FFC0CB', '#9ACD32', '#FF0000', '#40E0D0', '#48D1CC', 
            '#8A2BE2', '#C71585', '#FF1493', '#8B0000', '#FFD32C', 
            '#FF69B4'
        ]
        
        # Update visibility and colors
        for canton in cantons:
            if canton not in canton_to_idx:
                continue
                
            idx = canton_to_idx[canton]
            color_idx = idx % len(COLOR_SCALE)
            color = COLOR_SCALE[color_idx]
            
            if canton in selected_cantons:
                # Show colored line, hide grey line
                fig.data[idx * 3].visible = False      # Grey line
                fig.data[idx * 3 + 1].visible = True   # Colored line
                
                # Update connecting line color
                fig.data[idx * 3 + 2].line.color = color
                fig.data[idx * 3 + 2].line.width = 1.5
                
                # Update annotation color and weight
                fig.layout.annotations[idx].font.color = color
                fig.layout.annotations[idx].font.size = 12
                fig.layout.annotations[idx].font.family = font_family
            else:
                # Show grey line, hide colored line
                fig.data[idx * 3].visible = True       # Grey line
                fig.data[idx * 3 + 1].visible = False  # Colored line
                
                # Reset connecting line
                fig.data[idx * 3 + 2].line.color = 'rgba(191, 191, 191, 0.5)'  # GREY75
                fig.data[idx * 3 + 2].line.width = 1
                
                # Reset annotation
                fig.layout.annotations[idx].font.color = '#666666'  # GREY40
                fig.layout.annotations[idx].font.size = 10
                fig.layout.annotations[idx].font.family = font_family
        
        return fig
    
    return app

def main():
    # Load and process data.
    df = load_data(recreate_data=RECREATE_DATA)
    df = transform_data(df)
    df_filtered = filter_data(df)
    
    # Create and run the Dash application.
    app = create_dash_app(df_filtered)
    app.run_server(debug=True)

if __name__ == '__main__':
    main()
