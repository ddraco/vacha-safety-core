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
    
    # --- ЛОГИКА ЗА 7-ДНЕВЕН СИНХРОНИЗИРАН АНАЛИЗ ---
    # 1. Определяме крайния момент (най-новия запис)
    latest_dt = river_raw['dt_obj'].max()
    
    # Дефинираме липсващата променлива за subheader-а, за да не гърми
    latest_river_date_str = latest_dt.strftime('%d.%m.%Y') 
    
    # 2. Изчисляваме началния момент (преди 7 дни)
    start_dt = latest_dt - timedelta(days=7)

    # 3. Филтрираме и ДВАТА набора данни по времеви диапазон
    river = river_raw[(river_raw['dt_obj'] >= start_dt) & (river_raw['dt_obj'] <= latest_dt)].sort_values('dt_obj')
    
    # Подготовка на цените
    relevant_dates = river['dt_obj'].dt.strftime('%Y-%m-%d').unique()
    prices_filtered = prices_raw[prices_raw['Date'].isin(relevant_dates)].copy()
    
    # Сглобяваме datetime обекти за цените, за да се подредят по времевата ос X
    prices_filtered['dt_obj'] = pd.to_datetime(prices_filtered['Date'] + ' ' + prices_filtered['hour'].astype(str).str.zfill(2) + ':00')
    prices_hourly = prices_filtered.sort_values('dt_obj')

    st.subheader(f"📊 Седмичен анализ (Последно обновяване: {latest_river_date_str})")
    
    # ОСНОВНА ГРАФИКА (ДВЕ ОСИ)
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Линия на безопасност (вече е по цялата дължина на 7-те дни)
    fig.add_shape(
        type="line",
        x0=river['dt_obj'].min(), x1=river['dt_obj'].max(), y0=40, y1=40,
        line=dict(color="Red", width=3, dash="dash"),
        xref="x", yref="y",
        layer='above'
    )
    
    # Текст за линията (центриран спрямо 7-дневния период)
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

    # Настройки на мащабите и X-оста
    fig.update_yaxes(range=[0, 150], secondary_y=False) 
    fig.update_yaxes(range=[0, 350], secondary_y=True) # Малко по-висок диапазон за цените

    fig.update_layout(
        hovermode="x unified", 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=600 # Увеличаваме височината за по-добра видимост на 7 дни
    )
    
    # Форматираме оста X да показва ден и месец
    fig.update_xaxes(
        title_text="Дата и Час", 
        tickformat="%d.%m\n%H:%M",
        dtick=43200000/2 # Показва маркер на всеки 12 часа
    )
    
    st.plotly_chart(fig, use_container_width=True)
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