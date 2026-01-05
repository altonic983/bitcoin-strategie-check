import requests
import pandas as pd
import json
import numpy as np
from datetime import datetime

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1+rs))

def fetch_bitcoin_data():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=eur&days=365"
    data = requests.get(url).json()
    
    df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index('datetime')
    
    # 1. Tägliche Werte & MAs
    daily = df['price'].resample('D').last().to_frame()
    daily['ma30'] = daily['price'].rolling(30).mean()
    daily['ma50'] = daily['price'].rolling(50).mean()
    daily['ma200'] = daily['price'].rolling(200).mean()
    
    # 2. RSI berechnen (Neu!)
    daily['rsi'] = calculate_rsi(daily['price'])
    
    # 3. Abstand zum 365-Tage Hoch (Neu!)
    max_price = daily['price'].max()
    daily['dist_ath'] = ((daily['price'] / max_price) - 1) * 100
    
    recent = daily.dropna().tail(10)
    table_list = []
    
    for day, row in recent.iterrows():
        p, m30, m50, m200, rsi = row['price'], row['ma30'], row['ma50'], row['ma200'], row['rsi']
        
        # NEUE GEWICHTUNG (Beispiel):
        # MA200 (Trend) = 50% | MA50 (Momentum) = 30% | RSI (Stärke) = 20%
        score = 0
        if p > m200: score += 50
        if p > m50: score += 30
        if rsi < 60: score += 20 # RSI unter 60 gilt als gesund für Käufe
        
        table_list.append({
            "date": day.strftime('%d.%m.%Y'),
            "price": round(float(p), 2),
            "rsi": round(float(rsi), 1),
            "ath_dist": round(float(row['dist_ath']), 1),
            "ma200_ok": "Ja" if p > m200 else "Nein",
            "rating": "KAUFEN" if score >= 80 else "HALTEN" if score >= 50 else "WARTEN",
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
