import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Настройка за мобилни устройства
st.set_page_config(page_title="Vacha Safety Monitor", layout="wide")

st.title("📊 Мониторинг на язовир Въча")

# 2. Функция за зареждане на данни
def load_data():
    # Провери дали името на файла съвпада с това, което ботът записва!
    data_path = 'data/vacha_data.csv'
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        # Увери се, че колоната се казва 'datetime'
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        return df
    return None

df = load_data()

# 3. Настройки за мобилен скрол (най-важното за теб!)
config = {
    'scrollZoom': False,
    'displayModeBar': False,
    'staticPlot': False,
    'responsive': True
}

if df is not None:
    # --- ГРАФИКА НИВО ---
    fig_level = go.Figure()
    fig_level.add_trace(go.Scatter(
        x=df['datetime'], 
        y=df['level'], 
        mode='lines+markers',
        name='Ниво (m)',
        line=dict(color='#007bff')
    ))

    fig_level.update_layout(
        title="Ниво на водата (m)",
        margin=dict(l=5, r=5, t=40, b=80), # По-голям марж отдолу за легендата
        height=400,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
    )

    st.plotly_chart(fig_level, use_container_width=True, config=config)

    st.divider()

    # --- ГРАФИКА ОБЕМ (само ако има данни) ---
    if 'volume' in df.columns:
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(
            x=df['datetime'], 
            y=df['volume'], 
            mode='lines',
            name='Обем',
            line=dict(color='#28a745')
        ))
        
        fig_vol.update_layout(
            title="Обем на язовира",
            margin=dict(l=5, r=5, t=40, b=80),
            height=400,
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_vol, use_container_width=True, config=config)

    # --- ТАБЛИЦА ---
    st.subheader("📝 Последни измервания")
    st.dataframe(df.tail(10).sort_values(by='datetime', ascending=False), use_container_width=True)

else:
    st.warning("⚠️ Не намерих файл 'data/vacha_data.csv'. Провери дали ботът го е създал.")
