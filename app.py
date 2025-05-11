# dashboard_app.py
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

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
        percent_df[ab] = (df[resistant] / df[tested] * 100).round(2)
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
thresholds_other = compute_tukey_thresholds(df_other_percent)

# Streamlit dashboard
st.title("Staphylococcus aureus - Resistance to Other Antibiotics (Weekly, 2024)")

# Function to plot antibiotic resistance evolution
def plot_antibiotic(df, ab, threshold):
    fig, ax = plt.subplots()
    ax.plot(df['Week'], df[ab], marker='o', label=f"% Resistance - {ab}")
    ax.axhline(y=threshold, color='r', linestyle='--', label=f"Tukey Alert ({threshold}%)")
    # Mark alerts
    for i, val in enumerate(df[ab]):
        if val > threshold:
            ax.plot(df['Week'][i], val, 'ro', markersize=8)
    ax.set_title(f"Weekly Resistance for {ab}")
    ax.set_xlabel("Week")
    ax.set_ylabel("% Resistance")
    ax.set_ylim(0, 100)
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

# Plot each antibiotic
for ab in targets_other:
    plot_antibiotic(df_other_percent, ab, thresholds_other[ab])
