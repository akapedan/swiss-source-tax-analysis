import numpy as np
import plotly.graph_objects as go

def create_base_figure(df_filtered, canton_names=None, x_min=0, x_max=30000):
    """
    Create an interactive line plot for canton source tax rates using Plotly.
    
    Args:
        df_filtered (pd.DataFrame): Filtered DataFrame containing tax rate data
        canton_names (dict, optional): Mapping of canton codes to full names
        x_min (int): Minimum income value to display
        x_max (int): Maximum income value to display
    """
    # Color definitions
    GREY75 = 'rgba(191, 191, 191, 0.8)'  # Light grey with transparency
    GREY40 = '#666666'
    
    # Define consistent font
    font_family = 'Arial, Helvetica, sans-serif'
    
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
        
        # Main line (grey) - limit to x_max and start from x_min
        fig.add_trace(
            go.Scatter(
                x=data[(data['steuerbares_einkommen'] >= x_min) & 
                       (data['steuerbares_einkommen'] <= x_max)]['steuerbares_einkommen'],
                y=data[(data['steuerbares_einkommen'] >= x_min) & 
                       (data['steuerbares_einkommen'] <= x_max)]['steuer_prozent'],
                name=canton,
                line=dict(
                    color=GREY75,
                    width=1.5
                ),
                hovertemplate="Canton: %{text}<br>Income: %{x:,.0f} CHF<br>Tax Rate: %{y:.2f}%<extra></extra>",
                text=[canton] * len(data[(data['steuerbares_einkommen'] >= x_min) & 
                                        (data['steuerbares_einkommen'] <= x_max)]),
                legendgroup=canton,
                mode='lines',
                visible=True
            )
        )
        
        # Colored version of the line (initially hidden) - limit to x_max and start from x_min
        fig.add_trace(
            go.Scatter(
                x=data[(data['steuerbares_einkommen'] >= x_min) & 
                       (data['steuerbares_einkommen'] <= x_max)]['steuerbares_einkommen'],
                y=data[(data['steuerbares_einkommen'] >= x_min) & 
                       (data['steuerbares_einkommen'] <= x_max)]['steuer_prozent'],
                name=canton + "_colored",
                line=dict(
                    color=COLOR_SCALE[idx % len(COLOR_SCALE)],
                    width=2
                ),
                hovertemplate="Canton: %{text}<br>Income: %{x:,.0f} CHF<br>Tax Rate: %{y:.2f}%<extra></extra>",
                text=[canton] * len(data[(data['steuerbares_einkommen'] >= x_min) & 
                                        (data['steuerbares_einkommen'] <= x_max)]),
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

    # Create custom grid lines that start at x_min and stop at x_max
    x_grid_lines = []
    for x in np.linspace(x_min, x_max, 5):  # 5 grid lines from x_min to x_max
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
                x0=x_min,  # Start at x_min
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
    right_margin = max_label_length + 20  # Reduced multiplier and base value
    
    # Update layout
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        title=dict(
            text=f'Source Tax Rate Progression by Canton (2025) - Income Range: {x_min:,} - {x_max:,} CHF',
            x=0.5,
            font=dict(size=18, color=GREY40, family=font_family)
        ),
        xaxis=dict(
            title=dict(
                text='Monthly Taxable Income (CHF)',
                font=dict(size=12, color=GREY40, family=font_family)
            ),
            showgrid=False,  # Disable default grid
            zeroline=False,
            tickformat=',d',
            range=[x_min * 0.95, x_max * 1.22],  # Start from x_min with a small buffer
            tickfont=dict(family=font_family)
        ),
        yaxis=dict(
            title=dict(
                text='Source Tax Rate (%)',
                font=dict(size=12, color=GREY40, family=font_family)
            ),
            showgrid=False,  # Disable default grid
            zeroline=False,
            range=[y_min * 0.85 - padding, y_max * 1.15 + padding],  # Add extra padding
            tickfont=dict(family=font_family)
        ),
        showlegend=False,
        hovermode='closest',
        margin=dict(t=100, l=50, r=right_margin, b=50),
        shapes=x_grid_lines + y_grid_lines,  # Add custom grid lines
        font=dict(family=font_family),
        autosize=True  # Enable autosize for responsive behavior
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
    
    # Add x-axis ticks based on the range
    tick_count = 5
    tick_values = np.linspace(x_min, x_max, tick_count)
    tick_texts = [f'{int(val):,}' for val in tick_values]
    
    fig.update_xaxes(
        tickvals=tick_values,
        ticktext=tick_texts
    )
    
    return fig
