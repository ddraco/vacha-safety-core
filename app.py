import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os

# Настройки на страницата
st.set_page_config(page_title="Vacha Safety & Energy Analytics", layout="wide")
st.title("🌊 Vacha Safety: Мониторинг и Прогноза")

def load_data():
    # 1. Цени от IBEX
    df_e = pd.read_csv('data/energy_prices.csv', sep=';')
    df_e.columns = df_e.columns.str.strip()
    df_e['hour'] = df_e['Delivery Period'].str.slice(0, 2).astype(int)
    df_e['Date_dt'] = pd.to_datetime(df_e['Date'])
    
    # 2. Нива на реката
    df_r = pd.read_csv('data/vacha_levels.csv', skipinitialspace=True)
    
    # АВТОМАТИЧНО ПРЕИМЕНУВАНЕ (Оправя грешката с level_)
    df_r = df_r.rename(columns={col: 'level_cm' for col in df_r.columns if 'level' in col})
    
    df_r['date'] = df_r['date'].str.strip()
    # Сглобяваме обекта за времето
    df_r['dt_obj'] = pd.to_datetime(df_r['date'] + ' ' + df_r['hour'].astype(str).str.zfill(2) + ':00', dayfirst=True)
    
    return df_e, df_r

try:
    prices_raw, river_raw = load_data()
    
    # --- ЛОГИКА ЗА 7-ДНЕВЕН СИНХРОНИЗИРАН АНАЛИЗ ---
    latest_river_dt = river_raw['dt_obj'].max()
    latest_river_date_str = latest_river_dt.strftime('%d.%m.%Y')
    
    # Дефинираме период от точно 7 дни назад
    start_dt = latest_river_dt - timedelta(days=7)

    # Филтрираме реката и борсата
    river = river_raw[(river_raw['dt_obj'] >= start_dt) & (river_raw['dt_obj'] <= latest_river_dt)].sort_values('dt_obj')
    
    relevant_dates = river['dt_obj'].dt.strftime('%Y-%m-%d').unique()
    prices_filtered = prices_raw[prices_raw['Date'].isin(relevant_dates)].copy()
    
    prices_filtered['dt_obj'] = pd.to_datetime(prices_filtered['Date'] + ' ' + prices_filtered['hour'].astype(str).str.zfill(2) + ':00')
    prices_hourly = prices_filtered.sort_values('dt_obj')

    st.subheader(f"📊 Седмичен анализ: {start_dt.strftime('%d.%m')} - {latest_river_date_str}")
    
    # --- ОСНОВНА ГРАФИКА (ДВЕ ОСИ) ---
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Линия на безопасност (40см)
    fig.add_shape(
        type="line",
        x0=start_dt, x1=latest_river_dt, y0=40, y1=40,
        line=dict(color="Red", width=3, dash="dash"),
        xref="x", yref="y", layer='above'
    )
    
    fig.add_annotation(
        x=river['dt_obj'].mean(), y=30, 
        text="ГРАНИЦА ГАЗЕНЕ (40см)",
        showarrow=False, 
        font=dict(color="black", size=12, family="Arial Black")
    )

    # 2. Река (Синя зона)
    fig.add_trace(go.Scatter(
        x=river['dt_obj'], y=river['level_cm'], 
        name="Ниво Въча (см)", fill='tozeroy', 
        line=dict(color='#00CCFF', width=2)
    ), secondary_y=False)

    # 3. Цена на тока (Червена линия)
    fig.add_trace(go.Scatter(
        x=prices_hourly['dt_obj'], y=prices_hourly['Price (EUR/MWh)'], 
        name="Цена Ток (EUR)", 
        line=dict(color='rgba(255, 75, 75, 0.7)', width=4)
    ), secondary_y=True)

    # Динамичен мащаб на Y (ниво на водата)
    max_level = river['level_cm'].max()
    fig.update_yaxes(range=[0, max(150, max_level + 20)], secondary_y=False) 
    fig.update_yaxes(range=[0, 450], secondary_y=True)

    fig.update_layout(
        hovermode="x unified", 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=600,
        xaxis=dict(
            range=[start_dt, latest_river_dt], # Фиксираме Х-оста да не бяга
            type="date",
            tickformat="%d.%m\n%H:%M",
            dtick=43200000.0, # Маркер на всеки 12 часа
            tickangle=-45
        )
    )
    
    fig.update_yaxes(title_text="<b>Ниво (см)</b>", secondary_y=False)
    fig.update_yaxes(title_text="<b>Цена (EUR)</b>", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True, key="main_vacha_chart")

    # --- СЕКЦИЯ ПРОГНОЗА ---
    st.divider()
    tomorrow_dt = latest_river_dt + timedelta(days=1)
    tomorrow_str = tomorrow_dt.strftime('%Y-%m-%d')
    prices_tomorrow = prices_raw[prices_raw['Date'] == tomorrow_str].sort_values('hour')

    if not prices_tomorrow.empty:
        st.success(f"🔮 ПРОГНОЗА ЗА УТРЕШНИЯ ПРИЛИВ: {tomorrow_str}")
        st.write("Следи пиковете на цената – тогава ВЕЦ-ът вероятно ще отвори турбините.")
        
        fig_tom = go.Figure()
        fig_tom.add_trace(go.Scatter(
            x=prices_tomorrow['hour'], y=prices_tomorrow['Price (EUR/MWh)'],
            fill='tozeroy', line=dict(color='orange', width=3),
            name="Прогнозна цена"
        ))
        fig_tom.update_layout(
            height=300, 
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(tickmode='linear', tick0=0, dtick=1, title="Час")
        )
        st.plotly_chart(fig_tom, use_container_width=True, key="tomorrow_forecast_chart")
    else:
        st.info(f"ℹ️ Данните за утре ({tomorrow_str}) ще са налични след 14:30 ч. днес.")

except Exception as e:
    st.error(f"❌ Грешка при обработката: {e}")
    st.info("Провери структурата на CSV файловете в папка 'data/'.")