import numpy as np
import plotly.graph_objects as go

def create_base_figure(df_filtered, canton_names=None, x_min=0, x_max=30000, tarif_code='A0', church_tax='Y', num_children=0, translations=None):
    """
    Create an interactive line plot for canton source tax rates using Plotly.
    
    Args:
        df_filtered (pd.DataFrame): Filtered DataFrame containing tax rate data
        canton_names (dict, optional): Mapping of canton codes to full names
        x_min (int): Minimum income value to display
        x_max (int): Maximum income value to display
        tarif_code: Selected tariff code
        church_tax: Selected church tax option
        num_children: Number of children
        translations: Dictionary of translations
    """
    # Use default English translations if none provided
    if translations is None:
        translations = {
            'source_tax_progression': 'Source Tax Rate Progression by Canton (2025)',
            'monthly_income': 'Monthly Taxable Income (CHF)',
            'tax_rate': 'Source Tax Rate (%)',
            'income_range_text': 'Income Range',
            'tarif_code': 'Tariff Code',
            'church_tax': 'Church Tax Option',
            'number_of_children': 'Number of Children'
        }
    
    # Color definitions
    GREY75 = 'rgba(191, 191, 191, 0.8)'  # Light grey with transparency
    GREY40 = '#666666'
    
    # Define consistent font
    font_family = 'Arial, Helvetica, sans-serif'
    
    # Color scale for highlighted cantons
    COLOR_SCALE = [
        '#9A5CB4', '#3F8EFC', '#906C33', '#7B3A96', '#5D5D5D', 
        '#3E8E75', '#5EFF5E', '#F0E68C', '#888888', '#4CA64C', 
        '#A0522D', '#DDA0DD', '#FF00FF', '#000080', '#FFA500', 
        '#FFC0CB', '#9ACD32', '#FF0000', '#40E0D0', '#48D1CC', 
        '#8A2BE2', '#C71585', '#FF1493', '#8B0000', '#FFD32C', 
        '#FF69B4'
    ]
    
    # If no canton names provided, use the codes
    if canton_names is None:
        canton_names = {canton: canton for canton in df_filtered['kanton'].unique()}

    # Create figure
    fig = go.Figure()

    # Calculate y range based on the selected income range
    income_filtered_df = df_filtered[
        (df_filtered['steuerbares_einkommen'] >= x_min) & 
        (df_filtered['steuerbares_einkommen'] <= x_max)
    ]
    
    if len(income_filtered_df) > 0:
        y_max = income_filtered_df['steuer_prozent'].max()
        y_min = income_filtered_df['steuer_prozent'].min()
    else:
        # Fallback if no data in range
        y_max = df_filtered['steuer_prozent'].max()
        y_min = df_filtered['steuer_prozent'].min()
    
    # Create sorted list of cantons (for data mapping)
    cantons = sorted(df_filtered['kanton'].unique())
    canton_to_idx = {canton: idx for idx, canton in enumerate(cantons)}

    # Create display points (for visual layout)
    display_points = []
    for canton in cantons:
        data = df_filtered[df_filtered['kanton'] == canton]
        # Get the last data point before or at x_max + 1 (to match our extended data lines)
        data_filtered = data[data['steuerbares_einkommen'] <= x_max + 1]
        if len(data_filtered) > 0:
            y_val = data_filtered['steuer_prozent'].iloc[-1]
            x_val = data_filtered['steuerbares_einkommen'].iloc[-1]
        else:
            # Fallback if no data points below x_max + 1
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
    
    # Create custom grid lines that align with ticks
    x_tick_values = np.linspace(x_min, x_max, 6)  # Reduce from 5 to 6 evenly spaced ticks
    y_tick_values = np.linspace(y_min * 0.85, y_max * 1.15, 5)  # Reduce from 10 to 5 ticks

    # Create custom grid lines that align with ticks
    x_grid_lines = []
    for x in x_tick_values:
        x_grid_lines.append(
            dict(
                type="line",
                x0=x,
                y0=y_min * 0.85 - padding,
                x1=x,
                y1=y_max * 1.15 + padding,
                line=dict(
                    color="rgba(232, 232, 232, 1)",
                    width=1
                ),
                layer="below"  # Explicitly set to appear below traces
            )
        )

    y_grid_lines = []
    for y in y_tick_values:
        y_grid_lines.append(
            dict(
                type="line",
                x0=x_min,  # Start at x_min
                y0=y,
                x1=x_max,  # Stop at x_max
                y1=y,
                line=dict(
                    color="rgba(232, 232, 232, 1)",
                    width=1
                ),
                layer="below"  # Explicitly set to appear below traces
            )
        )

    # Calculate the maximum label length to set appropriate right margin
    max_label_length = max([len(canton_names.get(canton, canton)) for canton in cantons])
    right_margin = max_label_length + 20  # Reduced multiplier and base value
    
    # Create figure with grid lines in the layout
    fig = go.Figure(layout=dict(
        shapes=x_grid_lines + y_grid_lines + [
            # Add a vertical line at x_max to visually separate the grid from the labels
            dict(
                type="line",
                x0=x_max,
                y0=y_min * 0.85 - padding,
                x1=x_max,
                y1=y_max * 1.15 + padding,
                line=dict(
                    color="rgba(232, 232, 232, 1)",
                    width=1
                ),
                layer="below"  # Explicitly set to appear below traces
            )
        ]
    ))
    
    # Now add all the data traces
    # Create traces in alphabetical order (for correct mapping)
    for canton in cantons:
        idx = canton_to_idx[canton]
        data = df_filtered[df_filtered['kanton'] == canton]
        
        # Find the display point for this canton
        display_point = next(p for p in display_points if p['canton'] == canton)
        
        # Main line (grey) - extend slightly beyond x_min and x_max to ensure lines touch the boundaries
        fig.add_trace(
            go.Scatter(
                x=data[(data['steuerbares_einkommen'] >= x_min - 1) & 
                       (data['steuerbares_einkommen'] <= x_max + 1)]['steuerbares_einkommen'],
                y=data[(data['steuerbares_einkommen'] >= x_min - 1) & 
                       (data['steuerbares_einkommen'] <= x_max + 1)]['steuer_prozent'],
                name=canton,
                line=dict(
                    color=GREY75,
                    width=1.5,
                    shape='linear'  # Ensure linear interpolation between points
                ),
                connectgaps=True,  # Connect any gaps in the data
                hovertemplate="Canton: %{text}<br>Income: %{x:,.0f} CHF<br>Tax Rate: %{y:.2f}%<extra></extra>",
                text=[canton] * len(data[(data['steuerbares_einkommen'] >= x_min - 1) & 
                                        (data['steuerbares_einkommen'] <= x_max + 1)]),
                legendgroup=canton,
                mode='lines',
                visible=True
            )
        )
        
        # Colored version of the line (initially hidden) - extend slightly beyond x_min and x_max
        fig.add_trace(
            go.Scatter(
                x=data[(data['steuerbares_einkommen'] >= x_min - 1) & 
                       (data['steuerbares_einkommen'] <= x_max + 1)]['steuerbares_einkommen'],
                y=data[(data['steuerbares_einkommen'] >= x_min - 1) & 
                       (data['steuerbares_einkommen'] <= x_max + 1)]['steuer_prozent'],
                name=canton + "_colored",
                line=dict(
                    color=COLOR_SCALE[idx % len(COLOR_SCALE)],
                    width=2,
                    shape='linear'  # Ensure linear interpolation between points
                ),
                connectgaps=True,  # Connect any gaps in the data
                hovertemplate="Canton: %{text}<br>Income: %{x:,.0f} CHF<br>Tax Rate: %{y:.2f}%<extra></extra>",
                text=[canton] * len(data[(data['steuerbares_einkommen'] >= x_min - 1) & 
                                        (data['steuerbares_einkommen'] <= x_max + 1)]),
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
                size=10,
                family=font_family
            ),
            xanchor='left',  # Explicitly set left alignment
            yanchor='middle'
        )

    # Update layout (without adding shapes here)
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        title=dict(
            text=f'<b>{translations["source_tax_progression"]}</b>',
            x=0.5,
            font=dict(size=18, color='black', family=font_family, weight='bold')
        ),
        xaxis=dict(
            title=dict(
                text=translations["monthly_income"],
                font=dict(size=12, color='black', family=font_family)
            ),
            showgrid=False,  # Disable default grid
            zeroline=False,
            tickformat=',d',
            range=[x_min * 0.95, x_max * 1.22],  # Start from x_min with a small buffer
            tickfont=dict(family=font_family, color='black'),
            tickvals=x_tick_values,
            ticktext=[f"{int(val):,}".replace(',', "'") + " CHF" for val in x_tick_values]
        ),
        yaxis=dict(
            title=dict(
                text=translations["tax_rate"],
                font=dict(size=12, color='black', family=font_family)
            ),
            showgrid=False,  # Disable default grid
            zeroline=False,
            range=[y_min * 0.85 - padding, y_max * 1.15 + padding],  # Add extra padding
            tickfont=dict(family=font_family, color='black'),
            tickvals=y_tick_values,
            ticktext=[f'{val:.1f}%' for val in y_tick_values],  # Add % symbol to tick labels
            ticksuffix=''  # Remove default ticksuffix since we added % to each label
        ),
        showlegend=False,
        hovermode='closest',
        margin=dict(t=130, l=50, r=right_margin, b=50),  # Increased top margin for subtitle
        font=dict(family=font_family),
        autosize=True  # Enable autosize for responsive behavior
    )
    
    # Add subtitle with tariff code, church tax, and number of children
    subtitle_text = f'<b>{translations["tarif_code"]}</b> {tarif_code}, <b>{translations["church_tax"]}</b> {church_tax}, <b>{translations["number_of_children"]}</b> {num_children}'
    
    fig.add_annotation(
        x=0.5,
        y=1.05,
        xref='paper',
        yref='paper',
        text=subtitle_text,
        showarrow=False,
        font=dict(size=14, color='black', family=font_family),
        align='center'
    )
    
    # Add income range text
    fig.add_annotation(
        x=0.5,
        y=1.01,
        xref='paper',
        yref='paper',
        text=f'<b>{translations["income_range_text"]}:</b> {x_min:,}'.replace(',', "'") + f' - {x_max:,}'.replace(',', "'") + ' CHF',
        showarrow=False,
        font=dict(size=14, color='black', family=font_family),
        align='center'
    )
    
    return fig
