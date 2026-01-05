import requests
import pandas as pd
import json
from datetime import datetime

def fetch_bitcoin_data():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=eur&days=365"
    response = requests.get(url).json()
    
    # Daten einlesen
    df = pd.DataFrame(response['prices'], columns=['timestamp', 'price'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Index setzen (Das löst den Fehler definitiv)
    df = df.set_index('datetime')
    
    # Tägliche Werte für MAs
    df_daily = df['price'].resample('D').last().to_frame()
    df_daily['ma30'] = df_daily['price'].rolling(window=30).mean()
    df_daily['ma50'] = df_daily['price'].rolling(window=50).mean()
    df_daily['ma200'] = df_daily['price'].rolling(window=200).mean()
    
    # 12 Uhr Werte (Wir nehmen den Wert, der 12:00 am nächsten ist)
    df_12h = df.at_time('12:00').resample('D').first()
    
    # Nur die letzten 10 Tage für die Tabelle
    df_recent = df_daily.dropna(subset=['ma200']).tail(10)
    table_data = []
    
    for day in df_recent.index:
        price_now = df_recent.loc[day, 'price']
        m30, m50, m200 = df_recent.loc[day, 'ma30'], df_recent.loc[day, 'ma50'], df_recent.loc[day, 'ma200']
        
        # Deine Logik: 20% (30D), 33% (50D), 47% (200D)
        score = (20 if price_now > m30 else 0) + (33 if price_now > m50 else 0) + (47 if price_now > m200 else 0)
        
        table_data.append({
            "date": day.strftime('%d.%m.%Y'),
            "price_12h": round(float(df_12h.loc[day, 'price'] if day in df_12h.index else price_now), 2),
            "ma30_ok": "Ja" if price_now > m30 else "Nein",
            "ma50_ok": "Ja" if price_now > m50 else "Nein",
            "ma200_ok": "Ja" if price_now > m200 else "Nein",
            "rating": "KAUFEN" if score >= 70 else "Warten",
            "score": int(score)
        })

    output = {
        "labels": df_recent.index.strftime('%Y-%m-%d').tolist(),
        "prices": df_recent['price'].round(2).tolist(),
        "ma30": df_recent['ma30'].round(2).tolist(),
        "ma50": df_recent['ma50'].round(2).tolist(),
        "ma200": df_recent['ma200'].round(2).tolist(),
        "table": table_data[::-1],
        "last_update": datetime.now().strftime('%d.%m.%Y %H:%M')
    }
    
    with open('data.json', 'w') as f:
        json.dump(output, f)

if __name__ == "__main__":
    fetch_bitcoin_data()
