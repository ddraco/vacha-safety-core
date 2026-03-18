import requests
import pandas as pd
import os
import urllib3
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def sync_prices():
    print("⚡ Скрапване на цени (IBEX формат)...")
    path = 'data/energy_prices.csv'
    
    # Дефинираме обхват: отпреди 8 дни до утре включително
    now = datetime.now()
    start_str = (now - timedelta(days=8)).strftime("%Y-%m-%d")
    end_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    
    url = f"https://api.energy-charts.info/price?country=bg&start={start_str}&end={end_str}"
    
    try:
        res = requests.get(url, timeout=30, verify=False)
        res.raise_for_status()
        data = res.json()
        
        if 'price' not in data or not data['price']:
            print("⚠️ API-то не върна цени за този период.")
            return

        new_rows = []
        for i, ts in enumerate(data['unix_seconds']):
            dt = datetime.fromtimestamp(ts)
            qh = (dt.hour * 4) + (dt.minute // 15) + 1
            start_t = dt.strftime("%H:%M")
            end_t = (dt + timedelta(minutes=15)).strftime("%H:%M")
            
            new_rows.append({
                "Date": dt.strftime("%Y-%m-%d"),
                "Product": f"QH {qh}",
                "Delivery Period": f"{start_t} - {end_t}",
                "Price (EUR/MWh)": round(data['price'][i], 2),
                "Volume (MW)": 0.0
            })
            
        df_new = pd.DataFrame(new_rows)

        if os.path.exists(path):
            df_old = pd.read_csv(path, sep=';')
            # Сливаме и махаме дубликати по Дата и Период (пазим последното намерено)
            df_final = pd.concat([df_old, df_new]).drop_duplicates(subset=['Date', 'Delivery Period'], keep='last')
        else:
            df_final = df_new

        # СОРТИРАНЕ: Важно, за да не се обърква графиката
        df_final = df_final.sort_values(['Date', 'Delivery Period'])
        
        df_final.to_csv(path, sep=';', index=False)
        print(f"✅ Успех! Общо записи в базата: {len(df_final)}")
        print(f"📅 Последна дата в архива: {df_final['Date'].max()}")

    except Exception as e:
        print(f"❌ Грешка при цените: {e}")

def sync_river():
    print("🌊 Скрапване на нива на реката...")
    path = 'data/vacha_levels.csv'
    try:
        res = requests.get("https://plovdiv.meteo.bg/krichim/index.php", timeout=15, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        river_data = []
        for row in soup.find_all('tr'):
            cells = [c.get_text(strip=True) for c in row.find_all('td')]
            if len(cells) == 4 and "." in cells[0]:
                d = cells[0]
                if len(d.split('.')) == 2: d += f".{datetime.now().year}"
                river_data.append({"date": d, "hour": int(cells[1]), "level_cm": int(cells[2]), "flow_m3s": cells[3]})
        
        if river_data:
            df_new = pd.DataFrame(river_data)
            if os.path.exists(path):
                df_old = pd.read_csv(path)
                df_final = pd.concat([df_old, df_new]).drop_duplicates(subset=['date', 'hour'], keep='first')
            else:
                df_final = df_new
            df_final.to_csv(path, index=False)
            print(f"✅ Реката е обновена. Последно ниво: {df_final.iloc[0]['level_cm']} см")
    except Exception as e:
        print(f"❌ Грешка при реката: {e}")

if __name__ == "__main__":
    os.makedirs('data', exist_ok=True)
    sync_river()
    sync_prices()