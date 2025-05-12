for ab in selected_antibiotics:
    ab_data = df_long[df_long['Antibiotic'] == ab]
    ab_data = ab_data[ab_data['% Resistance'] <= 40]  # <--- ajout clé

    weeks = ab_data['Week']
    values = ab_data['% Resistance']

    fig.add_trace(go.Scatter(
        x=weeks,
        y=values,
        mode='lines+markers',
        name=ab,
        marker=dict(size=8),
        line=dict(width=3)
    ))

    fig.add_trace(go.Scatter(
        x=weeks[values > thresh[ab]['upper']],
        y=values[values > thresh[ab]['upper']],
        mode='markers',
        name=f"{ab} Alert",
        marker=dict(size=10, color='red', symbol='circle-open'),
        showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=weeks,
        y=[thresh[ab]['upper']] * len(weeks),
        mode='lines',
        name=f"{ab} Upper Alert ({thresh[ab]['upper']}%)",
        line=dict(dash='dash', color='red', width=2),
        showlegend=True
    ))

    fig.add_trace(go.Scatter(
        x=weeks,
        y=[thresh[ab]['lower']] * len(weeks),
        mode='lines',
        name=f"{ab} Lower Alert ({thresh[ab]['lower']}%)",
        line=dict(dash='dot', color='orange', width=2),
        showlegend=True
    ))
