import streamlit as st
import pandas as pd
import plotly.express as px

# Настройка на страницата
st.set_page_config(page_title="Vacha Safety", page_icon="🌊")

st.title("🌊 Vacha Safety Анализатор")

# Функция за зареждане
def load_vacha_data():
    df = pd.read_csv('data/vacha_levels.csv')
    # Сортираме по час, за да върви графиката от сутрин към вечер
    df = df.sort_values(by=['date', 'hour'])
    return df

try:
    data = load_vacha_data()
    
    # Визуализация
    fig = px.area(data, x='hour', y='level_cm', 
                 title="Промяна на нивото на реката",
                 labels={'hour': 'Час', 'level_cm': 'Ниво (см)'},
                 color_discrete_sequence=['#00CCFF'])
    
    # Добавяне на критична линия за безопасност (базирана на твоето "нормално" ниво)
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Безопасно ниво")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Автоматичен Алърт
    latest_diff = data['level_cm'].iloc[-1] - data['level_cm'].iloc[-2]
    if latest_diff > 20:
        st.error(f"⚠️ КРИТИЧНО ПОКАЧВАНЕ! Нивото се вдигна с {latest_diff} см!")
    
except Exception as e:
    st.warning("Моля, проверете формата на CSV файла.")
    st.code("date,hour,level_cm,flow_m3s")
