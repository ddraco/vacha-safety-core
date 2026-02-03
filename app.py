import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Vacha Safety - Correlation", layout="wide")

st.title("🌊 Vacha Safety: Корелация Река vs. Борса")

def load_data():
    # 1. Зареждане на цените от IBEX
    # Използваме sep=';', за да разпознае колоните правилно
    df_e = pd.read_csv('data/energy_prices.csv', sep=';')
    # Извличаме часа (първите две цифри от Delivery Period)
    df_e['hour'] = df_e['Delivery Period'].str.slice(0, 2).astype(int)
    # Осредняваме 15-минутните цени до почасови
    prices_hourly = df_e.groupby('hour')['Price (EUR/MWh)'].mean().reset_index()

    # 2. Зареждане на нивата на реката (твоя файл)
    df_r = pd.read_csv('data/vacha_levels.csv', skipinitialspace=True)
    df_r = df_r.sort_values(by='hour')
    
    return prices_hourly, df_r

try:
    prices, river = load_data()

    # Създаване на графика с две оси (Y1 и Y2)
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # СИНЯТА ЗОНА: Ниво на реката
    fig.add_trace(
        go.Scatter(x=river['hour'], y=river['level_cm'], 
                   name="Ниво на реката (см)", fill='tozeroy',
                   line=dict(color='#00CCFF', width=2)),
        secondary_y=False,
    )

    # ЧЕРВЕНАТА ЛИНИЯ: Цена на борсата
    fig.add_trace(
        go.Scatter(x=prices['hour'], y=prices['Price (EUR/MWh)'], 
                   name="Цена на тока (EUR/MWh)",
                   line=dict(color='red', width=4)),
        secondary_y=True,
    )

    # Оформяне на графиката
    fig.update_layout(
        title_text=f"Анализ за {river['date'].iloc[0]}",
        hovermode="x unified"
    )

    fig.update_xaxes(title_text="Час от денонощието")
    fig.update_yaxes(title_text="<b>Ниво на реката (см)</b>", secondary_y=False)
    fig.update_yaxes(title_text="<b>Цена на тока (EUR)</b>", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)

    # ЛОГИКА ЗА ПРЕДУПРЕЖДЕНИЕ
    st.divider()
    max_price_hour = prices.loc[prices['Price (EUR/MWh)'].idxmax(), 'hour']
    st.warning(f"💡 Пикова цена на тока днес е в **{max_price_hour}:00 ч.** Виж дали реката реагира след този час!")

except Exception as e:
    st.error(f"Грешка при визуализацията: {e}")
    st.info("Увери се, че в data/energy_prices.csv има заглавен ред: Date;Product;Delivery Period;Price (EUR/MWh);Volume (MW)")