import requests
import pandas as pd
import json
from datetime import datetime

def fetch_bitcoin_data():
    # Daten holen
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=eur&days=365"
    data = requests.get(url).json()
    
    # DataFrame bauen
    df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index('datetime')
    
    # Tägliche Kurse & MAs
    daily = df['price'].resample('D').last().to_frame()
    daily['ma30'] = daily['price'].rolling(30).mean()
    daily['ma50'] = daily['price'].rolling(50).mean()
    daily['ma200'] = daily['price'].rolling(200).mean()
    
    # Letzte 10 Tage filtern
    recent = daily.dropna().tail(10)
    table_list = []
    
    for day, row in recent.iterrows():
        p, m30, m50, m200 = row['price'], row['ma30'], row['ma50'], row['ma200']
        score = (20 if p > m30 else 0) + (33 if p > m50 else 0) + (47 if p > m200 else 0)
        
        table_list.append({
            "date": day.strftime('%d.%m.%Y'),
            "price_12h": round(float(p), 2),
            "ma30_ok": "Ja" if p > m30 else "Nein",
            "ma50_ok": "Ja" if p > m50 else "Nein",
            "ma200_ok": "Ja" if p > m200 else "Nein",
            "rating": "KAUFEN" if score >= 70 else "Warten",
            "score": int(score)
        })

    output = {
        "labels": recent.index.strftime('%Y-%m-%d').tolist(),
        "prices": recent['price'].round(2).tolist(),
        "ma30": recent['ma30'].round(2).tolist(),
        "ma50": recent['ma50'].round(2).tolist(),
        "ma200": recent['ma200'].round(2).tolist(),
        "table": table_list[::-1],
        "last_update": datetime.now().strftime('%d.%m.%Y %H:%M')
    }
    
    with open('data.json', 'w') as f:
        json.dump(output, f)

if __name__ == "__main__":
    fetch_bitcoin_data()
