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
    df_e.columns = df_e.columns.str.strip()
    # Превръщаме часа в число и датата в datetime обект
    df_e['hour'] = df_e['Delivery Period'].str.slice(0, 2).astype(int)
    df_e['Date_dt'] = pd.to_datetime(df_e['Date'])
    
    # 2. Нива на реката
    df_r = pd.read_csv('data/vacha_levels.csv', skipinitialspace=True)
    df_r['date'] = df_r['date'].str.strip()
    # СЪРЦЕТО НА ОПТИМИЗАЦИЯТА: Превръщаме в datetime за правилно сортиране
    df_r['dt_obj'] = pd.to_datetime(df_r['date'] + ' ' + df_r['hour'].astype(str).str.zfill(2) + ':00', dayfirst=True)
    
    return df_e, df_r

try:
    prices_raw, river_raw = load_data()
    
    # --- ЛОГИКА ЗА СИНХРОНИЗАЦИЯ ---
    # Намираме най-новата дата в данните за реката, без значение от подредбата на файла
    latest_river_dt = river_raw['dt_obj'].max()
    latest_river_date_str = latest_river_dt.strftime('%d.%m.%Y')
    target_date_iso = latest_river_dt.strftime('%Y-%m-%d')

    # Филтрираме реката и сортираме хронологично (от 00:00 към 23:00)
    river = river_raw[river_raw['date'] == latest_river_date_str].sort_values('dt_obj')
    
    # Филтрираме борсата за СЪЩАТА дата като реката
    prices_today = prices_raw[prices_raw['Date'] == target_date_iso]
    prices_hourly = prices_today.groupby('hour')['Price (EUR/MWh)'].mean().reset_index()

    st.subheader(f"📊 Текущ анализ за дата: {latest_river_date_str}")
    
    # ОСНОВНА ГРАФИКА (ДВЕ ОСИ)
    # ОСНОВНА ГРАФИКА (ДВЕ ОСИ)
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Добавяме линия на безопасност (Shape)
    fig.add_shape(
        type="line",
        x0=0, x1=23, y0=45, y1=45,
        line=dict(color="Red", width=3, dash="dash"),
        xref="x", yref="y",  # Свързваме я с лявата ос (Ниво)
        layer='above'
    )
    
    # Добавяме текст (Annotation) с правилни параметри
    fig.add_annotation(
        x=12, y=45, 
        text="ГРАНИЦА ГАЗЕНЕ (45см)",
        showarrow=False, 
        ay=-15,             # Отместване нагоре (отрицателна стойност)
        font=dict(color="red", size=12, family="Arial Black")
    )

    # 2. Река (Синя зона)
    fig.add_trace(go.Scatter(
        x=river['hour'], y=river['level_cm'], 
        name="Ниво Въча (см)", fill='tozeroy', 
        line=dict(color='#00CCFF', width=2)
    ), secondary_y=False)

    # 3. Цена на тока (Червена линия)
    fig.add_trace(go.Scatter(
        x=prices_hourly['hour'], y=prices_hourly['Price (EUR/MWh)'], 
        name="Цена Ток (EUR)", 
        line=dict(color='rgba(255, 75, 75, 0.7)', width=4)
    ), secondary_y=True)

    # 4. Фиксиране на мащабите
    fig.update_yaxes(range=[0, 150], secondary_y=False) 
    fig.update_yaxes(range=[0, 300], secondary_y=True)

    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(title_text="Час от денонощието", tickmode='linear', tick0=0, dtick=1)
    fig.update_yaxes(title_text="<b>Ниво (см)</b>", secondary_y=False)
    fig.update_yaxes(title_text="<b>Цена (EUR)</b>", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)

    # --- СЕКЦИЯ ПРОГНОЗА ---
    st.divider()
    tomorrow_dt = latest_river_dt + timedelta(days=1)
    tomorrow_str = tomorrow_dt.strftime('%Y-%m-%d')
    prices_tomorrow = prices_raw[prices_raw['Date'] == tomorrow_str].sort_values('hour')

    if not prices_tomorrow.empty:
        st.success(f"🔮 ПРОГНОЗА ЗА УТРЕШНИЯ ПРИЛИВ: {tomorrow_str}")
        st.write("Следи пиковете на цената – тогава ВЕЦ-ът вероятно ще отвори крановете.")
        
        fig_tom = go.Figure()
        fig_tom.add_trace(go.Scatter(
            x=prices_tomorrow['hour'], y=prices_tomorrow['Price (EUR/MWh)'],
            fill='tozeroy', line=dict(color='orange', width=3),
            name="Прогнозна цена"
        ))
        fig_tom.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_tom, use_container_width=True)
    else:
        st.info(f"ℹ️ Данните за утре ({tomorrow_str}) ще са налични след 14:30 ч. днес.")

except Exception as e:
    st.error(f"Грешка при обработката: {e}")
    st.info("Провери дали имената на колоните в CSV файловете съвпадат точно.")