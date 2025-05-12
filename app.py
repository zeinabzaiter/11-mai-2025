# dashboard_app.py
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

# Load data
weekly_other_path = "other Antibiotiques staph aureus.xlsx"
df_other = pd.read_excel(weekly_other_path)

# Clean column names
df_other.columns = df_other.columns.str.strip()

# Antibiotic mappings
targets_other = {
    'DAP': ('DAP', 'R DAP'),
    'CLIN': ('CLIN', 'R CLIN'),
    'SXT': ('SXT', 'R SXT'),
    'LZ': ('LZ', 'R LZ')
}

# Compute weekly % resistance
def compute_weekly_percent(df, ab_map):
    percent_df = pd.DataFrame()
    percent_df['Week'] = df['Week'] if 'Week' in df.columns else df['Semaine']
    for ab, (tested, resistant) in ab_map.items():
        percent_series = pd.to_numeric(df[resistant], errors='coerce') / pd.to_numeric(df[tested], errors='coerce') * 100
        percent_series = percent_series.replace([np.inf, -np.inf], np.nan).round(2)
        percent_df[ab] = percent_series
    return percent_df

# Compute Tukey thresholds (upper & lower)
def compute_tukey_thresholds(df_percent):
    thresholds = {}
    for ab in df_percent.columns[1:]:
        q1 = df_percent[ab].quantile(0.25)
        q3 = df_percent[ab].quantile(0.75)
        iqr = q3 - q1
        thresholds[ab] = {
            'upper': round(q3 + 1.5 * iqr, 2),
            'lower': round(max(q1 - 1.5 * iqr, 0), 2)
        }
    return thresholds

# Prepare data
df_other_percent = compute_weekly_percent(df_other, targets_other)
thresh = compute_tukey_thresholds(df_other_percent)
df_long = df_other_percent.melt(id_vars='Week', var_name='Antibiotic', value_name='% Resistance')
df_long.dropna(inplace=True)

# Streamlit app
st.set_page_config(layout="wide")
st.title("🦠 Staphylococcus aureus - Resistance to Other Antibiotics (Weekly, 2024)")

# Antibiotic selection
available_antibiotics = df_long['Antibiotic'].unique().tolist()
selected_antibiotics = st.multiselect(
    "Select antibiotics to display:",
    options=available_antibiotics,
    default=available_antibiotics
)

# Plot
fig = go.Figure()

for ab in selected_antibiotics:
    ab_data = df_long[df_long['Antibiotic'] == ab]
    weeks = ab_data['Week']
    values = ab_data['% Resistance']
    
    # Trace resistance line
    fig.add_trace(go.Scatter(
        x=weeks,
        y=values,
        mode='lines+markers',
        name=ab,
        marker=dict(size=8),
        line=dict(width=3)
    ))
    
    # Highlight points above upper threshold in red
    fig.add_trace(go.Scatter(
        x=weeks[values > thresh[ab]['upper']],
        y=values[values > thresh[ab]['upper']],
        mode='markers',
        name=f"{ab} Alert",
        marker=dict(size=10, color='red', symbol='circle-open'),
        showlegend=False
    ))

    # Upper threshold line
    fig.add_trace(go.Scatter(
        x=weeks,
        y=[thresh[ab]['upper']] * len(weeks),
        mode='lines',
        name=f"{ab} Upper Alert ({thresh[ab]['upper']}%)",
        line=dict(dash='dash', color='red', width=2),
        showlegend=True
    ))

    # Lower threshold line
    fig.add_trace(go.Scatter(
        x=weeks,
        y=[thresh[ab]['lower']] * len(weeks),
        mode='lines',
        name=f"{ab} Lower Alert ({thresh[ab]['lower']}%)",
        line=dict(dash='dot', color='orange', width=2),
        showlegend=True
    ))

# Layout
fig.update_layout(
    title="📈 Weekly % Resistance with Alert Thresholds",
    xaxis_title="Week",
    yaxis_title="% Resistance",
    yaxis=dict(range=[0, 40]),  # ← C'est ici que l'échelle est fixée
    template="plotly_white",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)


st.plotly_chart(fig, use_container_width=True)
