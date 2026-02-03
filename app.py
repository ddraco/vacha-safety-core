import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ... (запази функциите за зареждане от предния път) ...

def show_forecast():
    try:
        # Вземаме утрешната дата в подходящ формат
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        df_e = pd.read_csv('data/energy_prices.csv', sep=';')
        # Филтрираме само за утре (ако си качил данните)
        tomorrow_prices = df_e[df_e['Date'] == tomorrow]
        
        if not tomorrow_prices.empty:
            st.subheader(f"🔮 Прогноза за утре: {tomorrow}")
            
            # Намираме пиковете (цената над средната за деня)
            avg_price = tomorrow_prices['Price (EUR/MWh)'].mean()
            danger_hours = tomorrow_prices[tomorrow_prices['Price (EUR/MWh)'] > avg_price * 1.2]
            
            if not danger_hours.empty:
                st.error(f"⚠️ ВНИМАНИЕ: Очаква се ВЕЦ-ът да работи в интервалите:")
                hours_list = danger_hours['Delivery Period'].values
                st.write(", ".join(hours_list))
            
            # Малка графика за утрешните цени
            fig_tomorrow = go.Figure()
            fig_tomorrow.add_trace(go.Scatter(
                x=tomorrow_prices['Delivery Period'], 
                y=tomorrow_prices['Price (EUR/MWh)'],
                line=dict(color='orange', width=3),
                fill='tozeroy',
                name="Утрешна цена"
            ))
            st.plotly_chart(fig_tomorrow, use_container_width=True)
        else:
            st.info("ℹ️ Все още няма данни за утре. Качи новия файл от IBEX след 14:30 ч.")
            
    except Exception as e:
        st.error(f"Неуспешна прогноза: {e}")

# Извикване в основния интерфейс
if st.sidebar.button("Виж прогноза за утре"):
    show_forecast()