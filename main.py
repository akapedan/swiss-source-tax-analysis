import os
import subprocess
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pandarallel import pandarallel
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

# Initialize pandarallel for parallel processing.
pandarallel.initialize()

# Global flag to control data recreation
RECREATE_DATA = False  # Set to True to reprocess all TXT files, False to use existing CSV

def process_txt_files(input_folder="input", output_folder="output"):
    """
    Concatenates TXT files, cleans the raw data, and saves a cleaned CSV.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    combined_file = os.path.join(output_folder, "combined.txt")
    
    # Concatenate all TXT files into one file
    if os.name == 'nt':  # Windows
        subprocess.run(f'type {input_folder}\\*.txt > {combined_file}', shell=True)
    else:  # Unix-like systems
        subprocess.run(f'cat {input_folder}/*.txt > {combined_file}', shell=True)
    
    # Define column specifications and names based on documentation.
    colspecs = [
        (0, 2),     # Recordart
        (2, 4),     # Transaktionsart
        (4, 6),     # Kanton
        (6, 16),    # Code Tarif
        (16, 24),   # Datum gültig ab
        (24, 33),   # Steuerbares Einkommen ab Fr.
        (33, 42),   # Tarifschritt in Fr.
        (42, 43),   # Code Geschlecht
        (43, 45),   # Anzahl Kinder
        (45, 54),   # Mindeststeuer in Fr.
        (54, 59),   # Steuer %-Satz
        (59, 62)    # Code Status
    ]
    column_names = [
        'recordart', 'transaktionsart', 'kanton', 'code_tarif',
        'datum_gueltig_ab', 'steuerbares_einkommen', 'tarifschritt',
        'code_geschlecht', 'anzahl_kinder', 'mindeststeuer',
        'steuer_prozent', 'code_status'
    ]
    
    # Read the fixed-width file.
    df = pd.read_fwf(
        combined_file,
        colspecs=colspecs,
        names=column_names,
        skiprows=1,    # Skip header of the first file
        skipfooter=1,  # Skip footer of the last file
        engine='python'
    )
    
    # Clean whitespace in string columns.
    for col in df.select_dtypes(include=['object']):
        df[col] = df[col].str.strip()
    
    # Split 'code_tarif' into individual components.
    df['code_tarif_one'] = df['code_tarif'].str[0]
    df['code_tarif_two'] = df['code_tarif'].str[1]
    df['kirchensteuer'] = df['code_tarif'].str[2]
    
    # Determine if the second character is numeric.
    numeric_values = pd.to_numeric(df['code_tarif_two'], errors='coerce')
    df['is_integer'] = numeric_values.notna()
    
    # Create a combined 'tarif_code' based on conversion success.
    df['tarif_code'] = df.parallel_apply(
        lambda row: row['code_tarif_one'] + row['code_tarif_two']
                    if not row['is_integer'] else row['code_tarif_one'],
        axis=1
    )
    
    # Convert monetary values to decimals (assuming 2 decimal places).
    df['steuerbares_einkommen'] = df['steuerbares_einkommen'].astype(float) / 100
    df['mindeststeuer'] = df['mindeststeuer'].astype(float) / 100
    df['steuer_prozent'] = df['steuer_prozent'].astype(float) / 100
    
    # Remove the temporary combined file.
    os.remove(combined_file)
    
    # Save the cleaned DataFrame to CSV.
    cleaned_file = os.path.join(output_folder, "tar25_cleaned.csv")
    df.to_csv(cleaned_file, index=False)
    print(f"Data has been cleaned and saved to '{cleaned_file}'")
    return df

def load_data():
    """
    Loads cleaned data from CSV or processes raw TXT files if needed.
    """
    cleaned_file = 'output/tar25_cleaned.csv'
    if RECREATE_DATA or not os.path.exists(cleaned_file):
        print("Processing TXT files...")
        df = process_txt_files()
    else:
        print("Reading from existing CSV file...")
        df = pd.read_csv(cleaned_file)
    return df

def transform_data(df):
    """
    Applies any additional transformations to the DataFrame.
    """
    # (Optional) Convert date fields or apply further transformations if needed.
    return df

def filter_data(df):
    """
    Filters the data to include only records with:
      - No children (anzahl_kinder == 0)
      - Tarif code 'A'
      - Kirchensteuer 'N'
      - Taxable income below 14,000 CHF.
    Also saves the filtered data to CSV.
    """
    df_filtered = df[
        (df['anzahl_kinder'] == 0) &
        (df['tarif_code'] == 'A') &
        (df['kirchensteuer'] == 'N') &
        (df['steuerbares_einkommen'] < 10_001)
    ]
    output_filtered = 'output/tar25_cleaned_filtered.csv'
    df_filtered.to_csv(output_filtered, index=False)
    print(f"Filtered data saved to '{output_filtered}'")
    return df_filtered

def create_base_figure(df_filtered, canton_names=None):
    """
    Create an interactive line plot for canton source tax rates using Plotly.
    
    Args:
        df_filtered (pd.DataFrame): Filtered DataFrame containing tax rate data
        canton_names (dict, optional): Mapping of canton codes to full names
    """
    # Color definitions
    GREY75 = 'rgba(191, 191, 191, 0.5)'  # Light grey with transparency
    GREY40 = '#666666'
    
    # Color scale for highlighted cantons
    COLOR_SCALE = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    
    # If no canton names provided, use the codes
    if canton_names is None:
        canton_names = {canton: canton for canton in df_filtered['kanton'].unique()}

    # Create figure
    fig = go.Figure()

    # Calculate label positions
    x_max = 10000  # Set fixed x_max at 10,000
    y_max = df_filtered['steuer_prozent'].max()
    y_min = df_filtered['steuer_prozent'].min()
    
    # Create sorted list of cantons (for data mapping)
    cantons = sorted(df_filtered['kanton'].unique())
    canton_to_idx = {canton: idx for idx, canton in enumerate(cantons)}

    # Create display points (for visual layout)
    display_points = []
    for canton in cantons:
        data = df_filtered[df_filtered['kanton'] == canton]
        # Get the last data point before or at x_max
        data_filtered = data[data['steuerbares_einkommen'] <= x_max]
        if len(data_filtered) > 0:
            y_val = data_filtered['steuer_prozent'].iloc[-1]
            x_val = data_filtered['steuerbares_einkommen'].iloc[-1]
        else:
            # Fallback if no data points below x_max
            y_val = data['steuer_prozent'].iloc[0]
            x_val = data['steuerbares_einkommen'].iloc[0]
            
        display_points.append({
            'canton': canton,
            'y_start': y_val,
            'x_last': x_val,
            'idx': canton_to_idx[canton]
        })

    # Sort by y_start value
    display_points.sort(key=lambda x: x['y_start'])

    # Define label positions with more padding at top and bottom
    # Use 90% of the available space, leaving 5% padding at top and bottom
    y_range = y_max * 1.15 - y_min * 0.85
    padding = 0.05 * y_range
    y_positions = np.linspace(
        y_min * 0.85 + padding,  # Add padding at bottom
        y_max * 1.15 - padding,  # Subtract padding at top
        len(display_points)
    )
    
    # Assign positions to display points
    for i, point in enumerate(display_points):
        point['y_end'] = y_positions[i]

    # Define x-coordinates for the connecting lines with a larger gap
    x_start = x_max  # End of data
    x_mid = x_max * 1.03  # Midpoint for curve
    x_end = x_max * 1.1  # Position for end of line, well before labels
    x_label = x_max * 1.1  # Position for labels, with a significant gap
    
    # Create traces in alphabetical order (for correct mapping)
    for canton in cantons:
        idx = canton_to_idx[canton]
        data = df_filtered[df_filtered['kanton'] == canton]
        
        # Find the display point for this canton
        display_point = next(p for p in display_points if p['canton'] == canton)
        
        # Main line (grey) - limit to x_max
        fig.add_trace(
            go.Scatter(
                x=data[data['steuerbares_einkommen'] <= x_max]['steuerbares_einkommen'],
                y=data[data['steuerbares_einkommen'] <= x_max]['steuer_prozent'],
                name=canton,
                line=dict(
                    color=GREY75,
                    width=1.5
                ),
                hovertemplate="Canton: %{text}<br>Income: %{x:,.0f} CHF<br>Tax Rate: %{y:.2f}%<extra></extra>",
                text=[canton] * len(data[data['steuerbares_einkommen'] <= x_max]),
                legendgroup=canton,
                mode='lines',
                visible=True
            )
        )
        
        # Colored version of the line (initially hidden) - limit to x_max
        fig.add_trace(
            go.Scatter(
                x=data[data['steuerbares_einkommen'] <= x_max]['steuerbares_einkommen'],
                y=data[data['steuerbares_einkommen'] <= x_max]['steuer_prozent'],
                name=canton + "_colored",
                line=dict(
                    color=COLOR_SCALE[idx % len(COLOR_SCALE)],
                    width=2
                ),
                hovertemplate="Canton: %{text}<br>Income: %{x:,.0f} CHF<br>Tax Rate: %{y:.2f}%<extra></extra>",
                text=[canton] * len(data[data['steuerbares_einkommen'] <= x_max]),
                legendgroup=canton,
                mode='lines',
                visible=False,
                showlegend=False
            )
        )
        
        # Add connecting line with three points (like in the example)
        fig.add_trace(
            go.Scatter(
                x=[display_point['x_last'], x_mid, x_end],
                y=[display_point['y_start'], display_point['y_end'], display_point['y_end']],
                mode='lines',
                line=dict(
                    color=GREY75,
                    width=1,
                    dash='dash'
                ),
                hoverinfo='skip',
                showlegend=False,
                legendgroup=canton
            )
        )
        
        # Add annotation for label instead of scatter text
        fig.add_annotation(
            x=x_label,
            y=display_point['y_end'],
            text=canton_names.get(canton, canton),
            showarrow=False,
            font=dict(
                color=GREY40,
                size=10
            ),
            xanchor='left',  # Explicitly set left alignment
            yanchor='middle'
        )

    # Create custom grid lines that stop at x_max
    x_grid_lines = []
    for x in np.linspace(0, x_max, 6):  # 6 grid lines from 0 to x_max
        x_grid_lines.append(
            dict(
                type="line",
                x0=x,
                y0=y_min * 0.85,
                x1=x,
                y1=y_max * 1.15,
                line=dict(
                    color="rgba(232, 232, 232, 1)",
                    width=1
                )
            )
        )
    
    y_grid_lines = []
    for y in np.linspace(y_min * 0.85, y_max * 1.15, 10):  # 10 horizontal grid lines
        y_grid_lines.append(
            dict(
                type="line",
                x0=0,
                y0=y,
                x1=x_max,  # Stop at x_max
                y1=y,
                line=dict(
                    color="rgba(232, 232, 232, 1)",
                    width=1
                )
            )
        )
    
    # Calculate the maximum label length to set appropriate right margin
    max_label_length = max([len(canton_names.get(canton, canton)) for canton in cantons])
    right_margin = max_label_length * 2 + 20  # Reduced multiplier and base value
    
    # Update layout
    fig.update_layout(
        plot_bgcolor='rgba(250, 250, 250, 1)',
        paper_bgcolor='rgba(250, 250, 250, 1)',
        title=dict(
            text='Source Tax Rate Progression by Canton (No Children, Alleinstehend)',
            x=0.5,
            font=dict(size=14, color=GREY40)
        ),
        xaxis=dict(
            title=dict(
                text='Monthly Taxable Income (CHF)',
                font=dict(size=12, color=GREY40)
            ),
            showgrid=False,  # Disable default grid
            zeroline=False,
            tickformat=',d',
            range=[0, x_max * 1.22]  # Reduced range to minimize extra space
        ),
        yaxis=dict(
            title=dict(
                text='Source Tax Rate (%)',
                font=dict(size=12, color=GREY40)
            ),
            showgrid=False,  # Disable default grid
            zeroline=False,
            range=[y_min * 0.85 - padding, y_max * 1.15 + padding]  # Add extra padding
        ),
        showlegend=False,
        hovermode='closest',
        height=800,
        width=1600,
        margin=dict(t=100, l=50, r=right_margin, b=50),  # Reduced right margin
        shapes=x_grid_lines + y_grid_lines  # Add custom grid lines
    )
    
    # Add a vertical line at x_max to visually separate the grid from the labels
    fig.add_shape(
        type="line",
        x0=x_max,
        y0=y_min * 0.85 - padding,
        x1=x_max,
        y1=y_max * 1.15 + padding,
        line=dict(
            color="rgba(232, 232, 232, 1)",
            width=1
        )
    )
    
    # Add x-axis tick at 10,000
    fig.update_xaxes(
        tickvals=[0, 2000, 4000, 6000, 8000, 10000],
        ticktext=['0', '2,000', '4,000', '6,000', '8,000', '10,000']
    )
    
    return fig

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
        'LU': 'Lucerne (LU)',
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
        'ZH': 'Zurich (ZH)'
    }
    
    app = Dash(__name__)
    
    # Create sorted list of cantons
    cantons = sorted(df_filtered['kanton'].unique())
    
    # Add custom CSS styling
    app.layout = html.Div([
        html.Div([  # Container for dropdown
            dcc.Dropdown(
                id='canton-selector',
                options=[
                    {'label': canton_names.get(canton, canton), 'value': canton} 
                    for canton in cantons
                ],
                multi=True,
                placeholder="Select cantons...",
                style={
                    'width': '400px',
                    'backgroundColor': 'white',
                },
                optionHeight=35,
                maxHeight=600,
            )
        ], style={
            'width': '100%',
            'display': 'flex',
            'justifyContent': 'flex-end',
            'marginBottom': '20px',
            'marginRight': '350px'  # Increased to match the figure margin
        }),
        dcc.Graph(
            id='canton-plot',
            figure=create_base_figure(df_filtered, canton_names),
            style={
                'height': '800px',
                'width': '1600px'  # Increased to match the figure width
            }
        )
    ], style={
        'width': '100%',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'padding': '20px'
    })
    
    @app.callback(
        Output('canton-plot', 'figure'),
        Input('canton-selector', 'value')
    )
    def update_figure(selected_cantons):
        fig = create_base_figure(df_filtered, canton_names)
        
        if not selected_cantons:  # If no cantons selected, return all grey
            return fig
            
        # Get the indices of selected cantons
        cantons = sorted(df_filtered['kanton'].unique())
        canton_to_idx = {canton: idx for idx, canton in enumerate(cantons)}
        
        # Color scale for highlighted cantons
        COLOR_SCALE = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        # Update visibility and colors
        for canton in cantons:
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
        
        return fig
    
    return app

def main():
    # Load and process data.
    df = load_data()
    df = transform_data(df)
    df_filtered = filter_data(df)
    
    # Create and run the Dash application.
    app = create_dash_app(df_filtered)
    app.run_server(debug=True)

if __name__ == '__main__':
    main()
