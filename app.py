import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os

# 1. Настройки на страницата
st.set_page_config(page_title="Vacha Safety & Energy Analytics", layout="wide")
st.title("🌊 Vacha Safety: Мониторинг и Прогноза")

# Конфигурация за мобилни устройства (за всички графики)
mobile_config = {
    'scrollZoom': False,
    'displayModeBar': False,
    'staticPlot': True,
    'responsive': True
}

def load_data():
    # --- ЗАРЕЖДАНЕ НА ЦЕНИ (ENERGY) ---
    df_e = pd.read_csv('data/energy_prices.csv', sep=';')
    df_e = df_e.dropna(subset=['Date', 'Delivery Period', 'Price (EUR/MWh)'])
    df_e['dt_obj'] = pd.to_datetime(df_e['Date'] + ' ' + df_e['Delivery Period'].str.slice(0, 5))
    
    # --- ЗАРЕЖДАНЕ НА РЕКАТА (RIVER) ---
    df_r = pd.read_csv('data/vacha_levels.csv')
    df_r = df_r.dropna(subset=['date', 'hour', 'level_cm'])
    df_r = df_r.rename(columns={col: 'level_cm' for col in df_r.columns if 'level' in col})
    df_r['hour'] = df_r['hour'].astype(int)
    df_r['dt_obj'] = pd.to_datetime(
        df_r['date'].str.strip() + ' ' + df_r['hour'].astype(str).str.zfill(2) + ':00', 
        dayfirst=True
    )
    
    return df_e, df_r

try:
    prices_raw, river_raw = load_data()
    
    latest_river_dt = river_raw['dt_obj'].max()
    start_dt = latest_river_dt - timedelta(days=7)

    river = river_raw[river_raw['dt_obj'] >= start_dt].sort_values('dt_obj')
    prices = prices_raw[prices_raw['dt_obj'] >= start_dt].sort_values('dt_obj')

    st.subheader(f"📊 Седмичен анализ: {start_dt.strftime('%d.%m')} - {latest_river_dt.strftime('%d.%m.%Y')}")
    
    # --- ОСНОВНА ГРАФИКА (ДВЕ ОСИ) ---
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Линия на безопасност (40см)
    fig.add_shape(
        type="line",
        x0=start_dt, x1=latest_river_dt, y0=40, y1=40,
        line=dict(color="Red", width=3, dash="dash"),
        xref="x", yref="y", layer='above'
    )

    # 2. Река
    fig.add_trace(go.Scatter(
        x=river['dt_obj'], y=river['level_cm'], 
        name="Ниво Въча (см)", 
        fill='tozeroy', 
        line=dict(color='#00CCFF', width=2)
    ), secondary_y=False)

    # 3. Цена на тока
    fig.add_trace(go.Scatter(
        x=prices['dt_obj'], y=prices['Price (EUR/MWh)'], 
        name="Цена Ток (EUR)", 
        line=dict(color='rgba(255, 75, 75, 0.7)', width=4)
    ), secondary_y=True)

    max_level = river['level_cm'].max()
    fig.update_yaxes(range=[0, max(150, max_level + 20)], title_text="<b>Ниво (см)</b>", secondary_y=False)
    fig.update_yaxes(range=[0, 450], title_text="<b>Цена (EUR)</b>", secondary_y=True)

    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
        xaxis=dict(
            range=[start_dt, latest_river_dt],
            type="date",
            tickformat="%d.%m\n%H:%M",
            dtick=43200000.0,
            tickangle=-45
        )
    )
    
    st.plotly_chart(fig, use_container_width=True, config=mobile_config)

    # --- СЕКЦИЯ ПРОГНОЗА ЗА УТРЕ ---
    st.divider()
    tomorrow_dt = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0)
    tomorrow_str = tomorrow_dt.strftime('%Y-%m-%d')
    
    prices_tomorrow = prices_raw[prices_raw['Date'] == tomorrow_str].sort_values('dt_obj')

    if not prices_tomorrow.empty:
        st.success(f"🔮 ПРОГНОЗА ЗА УТРЕ: {tomorrow_dt.strftime('%d.%m.%Y')}")
        
        fig_tom = go.Figure()
        fig_tom.add_trace(go.Scatter(
            x=prices_tomorrow['dt_obj'], y=prices_tomorrow['Price (EUR/MWh)'],
            fill='tozeroy', line=dict(color='orange', width=3),
            name="Прогнозна цена"
        ))
        fig_tom.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(title="Час от денонощието")
        )
        st.plotly_chart(fig_tom, use_container_width=True, config=mobile_config)
    else:
        st.info(f"ℹ️ Прогнозата за утре ({tomorrow_dt.strftime('%d.%m')}) ще е налична след 14:30 ч.")

except Exception as e:
    st.error(f"❌ Грешка при визуализацията: {e}")
    st.info("💡 Увери се, че файловете в папка 'data/' съществуват.")
