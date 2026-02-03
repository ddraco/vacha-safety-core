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
    
    # ... тук остава кодът за графиката fig = make_subplots ...