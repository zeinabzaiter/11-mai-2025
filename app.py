# dashboard_app.py
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Load data file (update path as needed)
weekly_other_path = "other Antibiotiques staph aureus.xlsx"

# Load data
df_other = pd.read_excel(weekly_other_path)

# Clean column names
df_other.columns = df_other.columns.str.strip()

# Antibiotic mappings for column names and display
targets_other = {
    'DAP': ('DAP', 'R DAP'),
    'CLIN': ('CLIN', 'R CLIN'),
    'SXT': ('SXT', 'R SXT'),
    'LZ': ('LZ', 'R LZ')
}

def compute_weekly_percent(df, ab_map):
    percent_df = pd.DataFrame()
    percent_df['Week'] = df['Week'] if 'Week' in df.columns else df['Semaine']
    for ab, (tested, resistant) in ab_map.items():
        percent_series = pd.to_numeric(df[resistant], errors='coerce') / pd.to_numeric(df[tested], errors='coerce') * 100
        percent_series = percent_series.replace([np.inf, -np.inf], np.nan).round(2)
        percent_df[ab] = percent_series
    return percent_df

def compute_tukey_thresholds(df_percent):
    thresholds = {}
    for ab in df_percent.columns[1:]:
        q1 = df_percent[ab].quantile(0.25)
        q3 = df_percent[ab].quantile(0.75)
        iqr = q3 - q1
        thresholds[ab] = round(q3 + 1.5 * iqr, 2)
    return thresholds

# Prepare data
df_other_percent = compute_weekly_percent(df_other, targets_other)
thresh = compute_tukey_thresholds(df_other_percent)
df_long = df_other_percent.melt(id_vars='Week', var_name='Antibiotic', value_name='% Resistance')
df_long.dropna(inplace=True)

# Streamlit dashboard
st.title("Staphylococcus aureus - Resistance to Other Antibiotics (Weekly, 2024)")

# Antibiotic selection filter
available_antibiotics = df_long['Antibiotic'].unique().tolist()
selected_antibiotics = st.multiselect(
    "Select antibiotics to display:",
    options=available_antibiotics,
    default=available_antibiotics
)

# Interactive line chart with thresholds
fig = go.Figure()

for ab in selected_antibiotics:
    ab_data = df_long[df_long['Antibiotic'] == ab]
    fig.add_trace(go.Scatter(
        x=ab_data['Week'],
        y=ab_data['% Resistance'],
        mode='lines+markers',
        name=ab
    ))
    fig.add_trace(go.Scatter(
        x=ab_data['Week'],
        y=[thresh[ab]] * len(ab_data),
        mode='lines',
        name=f"Alert {ab} ({thresh[ab]}%)",
        line=dict(dash='dash', color='red'),
        showlegend=True
    ))

fig.update_layout(
    title="Weekly Resistance % by Antibiotic with Alert Thresholds",
    xaxis_title="Week",
    yaxis_title="% Resistance",
    yaxis_range=[0, 40],
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)
