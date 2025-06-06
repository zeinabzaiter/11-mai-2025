# dashboard_app.py
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

# Charger les données
weekly_other_path = "other Antibiotiques staph aureus.xlsx"
df_other = pd.read_excel(weekly_other_path)

# Nettoyer les noms de colonnes
df_other.columns = df_other.columns.str.strip()

# Mappage des antibiotiques
targets_other = {
    'DAP': ('DAP', 'R DAP'),
    'CLIN': ('CLIN', 'R CLIN'),
    'SXT': ('SXT', 'R SXT'),
    'LZ': ('LZ', 'R LZ')
}

# Calculer le pourcentage de résistance hebdomadaire
def compute_weekly_percent(df, ab_map):
    percent_df = pd.DataFrame()
    percent_df['Week'] = df['Week'] if 'Week' in df.columns else df['Semaine']
    for ab, (tested, resistant) in ab_map.items():
        tested_values = pd.to_numeric(df[tested], errors='coerce')
        resistant_values = pd.to_numeric(df[resistant], errors='coerce')
        percent_series = (resistant_values / tested_values) * 100
        percent_series = percent_series.replace([np.inf, -np.inf], np.nan)
        percent_series = percent_series.clip(upper=100).round(2)  # Limiter à 100%
        percent_df[ab] = percent_series
    return percent_df

# Calculer les seuils de Tukey (supérieur et inférieur)
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

# Préparer les données
df_other_percent = compute_weekly_percent(df_other, targets_other)
thresh = compute_tukey_thresholds(df_other_percent)
df_long = df_other_percent.melt(id_vars='Week', var_name='Antibiotic', value_name='% Resistance')
df_long.dropna(inplace=True)

# Application Streamlit
st.set_page_config(layout="wide")
st.title("🦠 Staphylococcus aureus - Résistance aux autres antibiotiques (Hebdomadaire, 2024)")

# Sélection des antibiotiques
available_antibiotics = df_long['Antibiotic'].unique().tolist()
selected_antibiotics = st.multiselect(
    "Sélectionnez les antibiotiques à afficher :",
    options=available_antibiotics,
    default=available_antibiotics
)

# Tracer le graphique
fig = go.Figure()

for ab in selected_antibiotics:
    ab_data = df_long[df_long['Antibiotic'] == ab]
    ab_data = ab_data[ab_data['% Resistance'] <= 100]  # Filtrer les valeurs aberrantes
    weeks = ab_data['Week']
    values = ab_data['% Resistance']

    # Ligne de résistance
    fig.add_trace(go.Scatter(
        x=weeks,
        y=values,
        mode='lines+markers',
        name=ab,
        marker=dict(size=8),
        line=dict(width=3)
    ))

    # Points d'alerte en rouge
    fig.add_trace(go.Scatter(
        x=weeks[values > thresh[ab]['upper']],
        y=values[values > thresh[ab]['upper']],
        mode='markers',
        name=f"Alerte {ab}",
        marker=dict(size=10, color='red', symbol='circle-open'),
        showlegend=False
    ))

    # Lignes de seuils
    fig.add_trace(go.Scatter(
        x=weeks,
        y=[thresh[ab]['upper']] * len(weeks),
        mode='lines',
        name=f"Seuil haut {ab} ({thresh[ab]['upper']}%)",
        line=dict(dash='dash', color='red', width=2),
        showlegend=True
    ))

    fig.add_trace(go.Scatter(
        x=weeks,
        y=[thresh[ab]['lower']] * len(weeks),
        mode='lines',
        name=f"Seuil bas {ab} ({thresh[ab]['lower']}%)",
        line=dict(dash='dot', color='orange', width=2),
        showlegend=True
    ))

# Forcer l'échelle de l'axe Y
fig.update_layout(
    title="📈 Pourcentage de résistance hebdomadaire avec seuils d'alerte",
    xaxis_title="Semaine",
    yaxis_title="% Résistance",
    yaxis=dict(
        range=[0, 40],
        fixedrange=True
    ),
    template="plotly_white",
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

st.plotly_chart(fig, use_container_width=True)
