import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os

# 1. Конфигурация
st.set_page_config(page_title="Vacha Safety Monitor", layout="wide")
CURRENT_MODEL = "gemini-2.5-flash"

# Общи настройки за графиките (за по-добър скрол на телефон)
mobile_config = {'scrollZoom': False, 'displayModeBar': False, 'staticPlot': False}

def load_data():
    # Зареждане на цени (Energy)
    df_e = pd.read_csv('data/energy_prices.csv', sep=';')
    df_e = df_e.dropna(subset=['Date', 'Delivery Period', 'Price (EUR/MWh)'])
    df_e['dt_obj'] = pd.to_datetime(df_e['Date'] + ' ' + df_e['Delivery Period'].str.slice(0, 5))
    
    # Зареждане на реката (River)
    df_r = pd.read_csv('data/vacha_levels.csv')
    df_r = df_r.dropna(subset=['date', 'hour', 'level_cm'])
    df_r = df_r.rename(columns={col: 'level_cm' for col in df_r.columns if 'level' in col})
    df_r['hour'] = df_r['hour'].astype(int)
    df_r['dt_obj'] = pd.to_datetime(df_r['date'].str.strip() + ' ' + df_r['hour'].astype(str).str.zfill(2) + ':00', dayfirst=True)
    
    return df_e, df_r

st.title("🌊 Vacha Safety: Мониторинг и Прогноза")

try:
    prices_raw, river_raw = load_data()
    
    # Филтриране за последната седмица
    latest_river_dt = river_raw['dt_obj'].max()
    start_dt = latest_river_dt - timedelta(days=7)
    river = river_raw[river_raw['dt_obj'] >= start_dt].sort_values('dt_obj')
    prices = prices_raw[prices_raw['dt_obj'] >= start_dt].sort_values('dt_obj')

    st.subheader(f"📊 Анализ: {start_dt.strftime('%d.%m')} - {latest_river_dt.strftime('%d.%m.%Y')}")

    # --- ГРАФИКА С ДВЕ ОСИ ---
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Линия на безопасност
    fig.add_shape(type="line", x0=start_dt, x1=latest_river_dt, y0=40, y1=40,
                  line=dict(color="Red", width=3, dash="dash"), layer='above')

    # Река (Ниво)
    fig.add_trace(go.Scatter(x=river['dt_obj'], y=river['level_cm'], name="Ниво (см)", 
                             fill='tozeroy', line=dict(color='#00CCFF', width=2)), secondary_y=False)

    # Цена на тока
    fig.add_trace(go.Scatter(x=prices['dt_obj'], y=prices['Price (EUR/MWh)'], name="Цена Ток (EUR)", 
                             line=dict(color='rgba(255, 75, 75, 0.7)', width=4)), secondary_y=True)

    # Настройки на оси
    max_level = river['level_cm'].max()
    fig.update_yaxes(range=[0, max(150, max_level + 20)], title_text="Ниво (см)", secondary_y=False)
    fig.update_yaxes(range=[0, 450], title_text="Цена (EUR)", secondary_y=True)

    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(tickformat="%d.%m\n%H:%M", tickangle=-45)
    )

    st.plotly_chart(fig, use_container_width=True, config=mobile_config)

    # --- ПРОГНОЗА ЗА УТРЕ ---
    st.divider()
    tomorrow_dt = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0)
    tomorrow_str = tomorrow_dt.strftime('%Y-%m-%d')
    prices_tomorrow = prices_raw[prices_raw['Date'] == tomorrow_str].sort_values('dt_obj')

    if not prices_tomorrow.empty:
        st.success(f"🔮 ПРОГНОЗА ЗА УТРЕ: {tomorrow_dt.strftime('%d.%m.%Y')}")
        fig_tom = go.Figure()
        fig_tom.add_trace(go.Scatter(x=prices_tomorrow['dt_obj'], y=prices_tomorrow['Price (EUR/MWh)'],
                                     fill='tozeroy', line=dict(color='orange', width=3)))
        fig_tom.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_tom, use_container_width=True, config=mobile_config)
    else:
        st.info(f"ℹ️ Прогнозата за утре ще е налична след 14:30 ч.")

    # Таблица
    st.subheader("📝 Последни измервания")
    st.dataframe(river.tail(10).sort_values(by='dt_obj', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"❌ Грешка: {e}")
    st.info("💡 Провери дали файловете в папка 'data/' съществуват.")
