import requests
import pandas as pd
import json
from datetime import datetime

def fetch_bitcoin_data():
    # 1. Daten von CoinGecko holen
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=eur&days=365"
    response = requests.get(url).json()
    
    # Preise extrahieren und DataFrame erstellen
    df = pd.DataFrame(response['prices'], columns=['timestamp', 'price'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # WICHTIG: Datetime als Index setzen für stabiles Resampling
    df = df.set_index('datetime')
    
    # 2. Moving Averages berechnen (Tägliche Basis)
    df_daily = df['price'].resample('D').last().to_frame()
    df_daily['ma30'] = df_daily['price'].rolling(window=30).mean()
    df_daily['ma50'] = df_daily['price'].rolling(window=50).mean()
    df_daily['ma200'] = df_daily['price'].rolling(window=200).mean()
    
    # 3. 12:00 Uhr Logik für die Tabelle
    # Wir filtern alle Datenpunkte zwischen 11:00 und 13:00 Uhr und nehmen den ersten pro Tag
    df_12h_raw = df[(df.index.hour >= 11) & (df.index.hour <= 13)]
    df_12h = df_12h_raw.resample('D').first()
    
    # Zusammenführen für die letzten 10 Tage
    latest_days = []
    # Wir nehmen die letzten 10 Tage, die einen 200D MA haben
    df_recent = df_daily.dropna(subset=['ma200']).tail(10)
    relevant_days = df_recent.index
    
    for day in relevant_days:
        current_price = df_recent.loc[day, 'price']
        m30 = df_recent.loc[day, 'ma30']
        m50 = df_recent.loc[day, 'ma50']
        m200 = df_recent.loc[day, 'ma200']
        
        check30 = current_price > m30
        check50 = current_price > m50
        check200 = current_price > m200
        
        score = 0
        if check30: score += 20
        if check50: score += 33
        if check200: score += 47
        
        # Preis um 12 Uhr finden oder Fallback auf Tagesschluss
        p12 = df_12h.loc[day, 'price'] if day in df_12h.index else current_price
        
        latest_days.append({
            "date": day.strftime('%d.%m.%Y'),
            "price_12h": round(float(p12), 2),
            "ma30_ok": "Ja" if check30 else "Nein",
            "ma50_ok": "Ja" if check50 else "Nein",
            "ma200_ok": "Ja" if check200 else "Nein",
            "rating": "KAUFEN" if score >= 70 else "Warten",
            "score": int(score)
        })

    # 4. Daten für Chart exportieren
    chart_data = {
        "labels": df_recent.index.strftime('%Y-%m-%d').tolist(),
        "prices": df_recent['price'].round(2).tolist(),
        "ma30": df_recent['ma30'].round(2).tolist(),
        "ma50": df_recent['ma50'].round(2).tolist(),
        "ma200": df_recent['ma200'].round(2).tolist(),
        "table": latest_days[::-1],
        "last_update": datetime.now().strftime('%d.%m.%Y %H:%M')
    }
    
    with open('data.json', 'w') as f:
        json.dump(chart_data, f)

if __name__ == "__main__":
    fetch_bitcoin_data()
