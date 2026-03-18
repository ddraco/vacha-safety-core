import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import urllib3
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def sync_river():
    print("🌊 Скрапване на нивото...")
    url = "https://plovdiv.meteo.bg/krichim/index.php"
    try:
        res = requests.get(url, timeout=15, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.find_all('tr')
        new_data = []
        for row in rows:
            cells = [c.get_text(strip=True) for c in row.find_all('td')]
            if len(cells) == 4 and "." in cells[0]:
                date_val = f"{cells[0].strip()}.2026" if "2026" not in cells[0] else cells[0].strip()
                new_data.append({
                    "date": date_val,
                    "hour": int(cells[1]),
                    "level_cm": int(cells[2]),
                    "flow_m3s": cells[3].replace('m3/s', '').strip()
                })
        if new_data:
            df_new = pd.DataFrame(new_data)
            path = 'data/vacha_levels.csv'
            if os.path.exists(path):
                df_old = pd.read_csv(path)
                df_new = pd.concat([df_old, df_new]).drop_duplicates(subset=['date', 'hour'], keep='first')
            df_new.to_csv(path, index=False)
            print("✅ Нивото е обновено.")
    except Exception as e: print(f"❌ Грешка река: {e}")

def sync_prices():
    print("⚡ Скрапване на цени (Формат IBEX)...")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    url = f"https://api.energy-charts.info/price?country=bg&start={start_date}"
    try:
        res = requests.get(url, timeout=30, verify=False)
        data = res.json()
        new_rows = []
        for i, ts in enumerate(data['unix_seconds']):
            dt = datetime.fromtimestamp(ts)
            start_t = dt.strftime("%H:%M")
            end_t = (dt + timedelta(minutes=15)).strftime("%H:%M")
            new_rows.append({
                "Date": dt.strftime("%Y-%m-%d"),
                "Product": f"QH {(dt.hour * 4) + (dt.minute // 15) + 1}",
                "Delivery Period": f"{start_t} - {end_t}",
                "Price (EUR/MWh)": round(data['price'][i], 2),
                "Volume (MW)": 0.0
            })
        df_new = pd.DataFrame(new_rows)
        path = 'data/energy_prices.csv'
        if os.path.exists(path):
            df_old = pd.read_csv(path, sep=';')
            df_new = pd.concat([df_old, df_new]).drop_duplicates(subset=['Date', 'Delivery Period'], keep='last')
        # ЗАПИСВАМЕ СЪС СЕПАРАТОР ";" ЗА ДА РАБОТИ ТВОЯ APP.PY
        df_new.to_csv(path, sep=';', index=False)
        print("✅ Цените са обновени.")
    except Exception as e: print(f"❌ Грешка цени: {e}")

if __name__ == "__main__":
    os.makedirs('data', exist_ok=True)
    sync_river()
    sync_prices()