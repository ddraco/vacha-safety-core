import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# Настройка на страницата за мобилни устройства
st.set_page_config(page_title="Vacha Safety Monitor", layout="wide")

st.title("📊 Мониторинг на язовир Въча")

# Функция за зареждане на данни
def load_data():
    data_path = 'data/vacha_data.csv'
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df
    return None

df = load_data()

if df is not None:
    # 1. ГРАФИКА ЗА НИВОТО
    fig_level = go.Figure()
    fig_level.add_trace(go.Scatter(
        x=df['datetime'], 
        y=df['level'], 
        mode='lines+markers',
        name='Ниво (m)',
        line=dict(color='#007bff')
    ))

    # Оптимизация за телефон
    config = {
        'scrollZoom': False,        # Забранява зум със скрол
        'displayModeBar': False,    # Скрива досадните иконки отгоре
        'staticPlot': False,        # Позволява кликане, но не и местене
    }

    fig_level.update_layout(
        title="Ниво на водата (m)",
        xaxis_title="Време",
        yaxis_title="Метри",
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5)
    )

    st.plotly_chart(fig_level, use_container_width=True, config=config)

    st.divider() # Малко разстояние между графиките

    # 2. ГРАФИКА ЗА ОБЕМ (ако имаш такава колона)
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
            margin=dict(l=10, r=10, t=40, b=10),
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_vol, use_container_width=True, config=config)

    # Таблица с последните данни
    st.subheader("📝 Последни измервания")
    st.dataframe(df.tail(10).sort_values(by='datetime', ascending=False), use_container_width=True)

else:
    st.error("Все още няма събрани данни в папка data/. Изчакай бота да рънне!")
