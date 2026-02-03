import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="Vacha Safety", layout="wide")
st.title("🌊 Vacha Safety: Мониторинг и Прогноза")

def load_data():
    # 1. Цени от IBEX
    df_e = pd.read_csv('data/energy_prices.csv', sep=';')
    # Почистваме заглавията (ако има интервали)
    df_e.columns = df_e.columns.str.strip()
    df_e['hour'] = df_e['Delivery Period'].str.slice(0, 2).astype(int)
    
    # 2. Нива на реката
    df_r = pd.read_csv('data/vacha_levels.csv', skipinitialspace=True)
    df_r['date'] = df_r['date'].str.strip()
    return df_e, df_r

try:
    prices_raw, river_raw = load_data()
    
    # 1. Намираме коя е последната налична дата в данните за реката
    latest_river_date = river_raw['date'].iloc[-1]
    
    # 2. Филтрираме и двата датафрейма само за тази дата
    river = river_raw[river_raw['date'] == latest_river_date]
    
    # За борсата филтрираме същата дата (но внимаваме с формата на датата)
    # Ако в реката е 03.02.2026, а в борсата 2026-02-03, преобразуваме:
    prices_today = prices_raw[prices_raw['Date'].str.contains(datetime.now().strftime('%Y-%m-%d'))]
    prices_hourly = prices_today.groupby('hour')['Price (EUR/MWh)'].mean().reset_index()

    st.subheader(f"📊 Текущ анализ за дата: {latest_river_date}")
    
    # ОСНОВНА ГРАФИКА (ДВЕ ОСИ)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=river['hour'], y=river['level_cm'], name="Ниво (см)", fill='tozeroy', line=dict(color='#00CCFF')), secondary_y=False)
    fig.add_trace(go.Scatter(x=prices_hourly['hour'], y=prices_hourly['Price (EUR/MWh)'], name="Цена (EUR)", line=dict(color='red', width=3)), secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)

    # --- СЕКЦИЯ ПРОГНОЗА ---
    st.divider()
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    prices_tomorrow = prices_raw[prices_raw['Date'] == tomorrow_str]

    if not prices_tomorrow.empty:
        st.success(f"🔮 НАМЕРЕНИ ДАННИ ЗА УТРЕ: {tomorrow_str}")
        # Тук сложи същия код за малката оранжева графика от предния път
        fig_tom = go.Figure(go.Scatter(x=prices_tomorrow['Delivery Period'], y=prices_tomorrow['Price (EUR/MWh)'], fill='tozeroy', line=dict(color='orange')))
        st.plotly_chart(fig_tom, use_container_width=True)
    else:
        st.info(f"ℹ️ Очакваме данни за утре ({tomorrow_str}). Качи ги от IBEX след 14:30 ч.")

except Exception as e:
    st.error(f"Грешка: {e}")
