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
      - Taxable income below 15,000 CHF.
    Also saves the filtered data to CSV.
    """
    df_filtered = df[
        (df['anzahl_kinder'] == 0) &
        (df['tarif_code'] == 'A') &
        (df['kirchensteuer'] == 'N') &
        (df['steuerbares_einkommen'] < 15_000)
    ]
    output_filtered = 'output/tar25_cleaned_filtered.csv'
    df_filtered.to_csv(output_filtered, index=False)
    print(f"Filtered data saved to '{output_filtered}'")
    return df_filtered

def create_base_figure(df_filtered):
    """
    Creates an interactive Plotly figure for canton tax rates.
    """
    # Color definitions.
    GREY75 = 'rgba(191, 191, 191, 0.5)'
    GREY40 = '#666666'
    COLOR_SCALE = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    
    fig = go.Figure()
    x_max = df_filtered['steuerbares_einkommen'].max()
    y_max = df_filtered['steuer_prozent'].max()
    y_min = df_filtered['steuer_prozent'].min()
    y_range = y_max * 1.15 - y_min * 0.85
    x_end = x_max * 1.12
    
    cantons = sorted(df_filtered['kanton'].unique())
    canton_to_idx = {canton: idx for idx, canton in enumerate(cantons)}
    
    # Calculate display positions for labels.
    display_points = []
    for canton in cantons:
        data = df_filtered[df_filtered['kanton'] == canton]
        y_val = data['steuer_prozent'].iloc[-1]
        display_points.append({'canton': canton, 'y_start': y_val, 'idx': canton_to_idx[canton]})
    display_points.sort(key=lambda x: x['y_start'])
    
    for i, point in enumerate(display_points):
        position = i / (len(display_points) - 1) if len(display_points) > 1 else 0
        if i < len(display_points) / 2:
            transformed_pos = np.power(position * 2, 1.5) / 2
        else:
            transformed_pos = 1 - np.power((1 - position) * 2, 1.5) / 2
        point['y_end'] = y_min * 0.85 + transformed_pos * y_range
    
    # Build traces for each canton.
    for canton in cantons:
        idx = canton_to_idx[canton]
        data = df_filtered[df_filtered['kanton'] == canton]
        display_point = next(p for p in display_points if p['canton'] == canton)
        
        # Grey line.
        fig.add_trace(go.Scatter(
            x=data['steuerbares_einkommen'],
            y=data['steuer_prozent'],
            name=canton,
            line=dict(color=GREY75, width=1.5),
            hovertemplate="Canton: %{text}<br>Income: %{x:,.0f} CHF<br>Tax Rate: %{y:.2f}%<extra></extra>",
            text=[canton] * len(data),
            legendgroup=canton,
            mode='lines',
            visible=True
        ))
        
        # Colored line (hidden by default).
        fig.add_trace(go.Scatter(
            x=data['steuerbares_einkommen'],
            y=data['steuer_prozent'],
            name=canton + "_colored",
            line=dict(color=COLOR_SCALE[idx % len(COLOR_SCALE)], width=2),
            hovertemplate="Canton: %{text}<br>Income: %{x:,.0f} CHF<br>Tax Rate: %{y:.2f}%<extra></extra>",
            text=[canton] * len(data),
            legendgroup=canton,
            mode='lines',
            visible=False,
            showlegend=False
        ))
        
        # Connecting line to label.
        PAD = x_max * 0.005
        fig.add_trace(go.Scatter(
            x=[x_max, (x_max + x_end - PAD) / 2, x_end - PAD],
            y=[display_point['y_start'], display_point['y_end'], display_point['y_end']],
            mode='lines',
            line=dict(color=GREY75, width=1, dash='dash'),
            hoverinfo='skip',
            showlegend=False,
            legendgroup=canton
        ))
        
        # Canton label.
        fig.add_trace(go.Scatter(
            x=[x_end],
            y=[display_point['y_end']],
            mode='text',
            text=[canton],
            textposition="middle right",
            textfont=dict(color=GREY40, size=10),
            hoverinfo='skip',
            showlegend=False,
            legendgroup=canton
        ))
    
    # Update layout.
    fig.update_layout(
        plot_bgcolor='rgba(250, 250, 250, 1)',
        paper_bgcolor='rgba(250, 250, 250, 1)',
        title=dict(
            text='Tax Rate Progression by Canton (No Children, Tarif Code A)',
            x=0.5,
            font=dict(size=14, color=GREY40)
        ),
        xaxis=dict(
            title=dict(text='Taxable Income (CHF)', font=dict(size=12, color=GREY40)),
            gridcolor='rgba(232, 232, 232, 1)',
            showgrid=True,
            zeroline=False,
            tickformat=',d'
        ),
        yaxis=dict(
            title=dict(text='Tax Rate (%)', font=dict(size=12, color=GREY40)),
            gridcolor='rgba(232, 232, 232, 1)',
            showgrid=True,
            zeroline=False
        ),
        showlegend=False,
        hovermode='closest',
        height=800,
        width=1400,
        margin=dict(t=100, l=50, r=150, b=50)
    )
    
    return fig

def create_dash_app(df_filtered):
    """
    Creates and configures a Dash application for interactive visualization.
    """
    app = Dash(__name__)
    
    app.layout = html.Div([
        html.Div([
            dcc.Dropdown(
                id='canton-selector',
                options=[{'label': canton, 'value': canton} for canton in sorted(df_filtered['kanton'].unique())],
                multi=True,
                placeholder="Select cantons...",
                style={'width': '400px', 'backgroundColor': 'white'},
                optionHeight=35,
                maxHeight=600,
            )
        ], style={'width': '100%', 'display': 'flex', 'justifyContent': 'flex-end',
                  'marginBottom': '20px', 'marginRight': '150px'}),
        dcc.Graph(
            id='canton-plot',
            figure=create_base_figure(df_filtered),
            style={'height': '800px', 'width': '1400px'}
        )
    ], style={'width': '100%', 'display': 'flex', 'flexDirection': 'column',
              'alignItems': 'center', 'padding': '20px'})
    
    @app.callback(
        Output('canton-plot', 'figure'),
        Input('canton-selector', 'value')
    )
    def update_figure(selected_cantons):
        fig = create_base_figure(df_filtered)
        
        if not selected_cantons:
            return fig
        
        # Update traces based on selected cantons.
        cantons = sorted(df_filtered['kanton'].unique())
        canton_to_idx = {canton: idx for idx, canton in enumerate(cantons)}
        
        for canton in cantons:
            idx = canton_to_idx[canton]
            if canton in selected_cantons:
                # Hide grey line; show colored line.
                fig.data[idx * 4].visible = False
                fig.data[idx * 4 + 1].visible = True
            else:
                # Show grey line; hide colored line.
                fig.data[idx * 4].visible = True
                fig.data[idx * 4 + 1].visible = False
        
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
