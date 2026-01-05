import requests
import pandas as pd
import json
from datetime import datetime

def fetch_bitcoin_data():
    # 1. Daten von CoinGecko holen (letzte 365 Tage für 200D MA)
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=eur&days=365"
    response = requests.get(url).json()
    
    # Preise extrahieren
    df = pd.DataFrame(response['prices'], columns=['timestamp', 'price'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # 2. Moving Averages berechnen (Daily Basis)
    # Wir brauchen tägliche Schlusskurse für saubere SMAs
    df_daily = df.resample('D', on='datetime').last()
    df_daily['ma30'] = df_daily['price'].rolling(window=30).mean()
    df_daily['ma50'] = df_daily['price'].rolling(window=50).mean()
    df_daily['ma200'] = df_daily['price'].rolling(window=200).mean()
    
    # 3. 12:00 Uhr Logik für die Tabelle
    # Wir suchen den Kurs, der 12:00 Uhr am nächsten kommt
    df['hour'] = df['datetime'].dt.hour
    df_12h = df[df['hour'] == 12].resample('D', on='datetime').first()
    
    # Zusammenführen für die letzten 10 Tage
    latest_days = []
    relevant_days = df_daily.tail(10).index
    
    for day in relevant_days:
        current_price = df_daily.loc[day, 'price']
        m30 = df_daily.loc[day, 'ma30']
        m50 = df_daily.loc[day, 'ma50']
        m200 = df_daily.loc[day, 'ma200']
        
        # Prüfung: Ist der Kurs ÜBER dem MA?
        check30 = current_price > m30
        check50 = current_price > m50
        check200 = current_price > m200
        
        # 4. Gewichtete Kauf-Logik (20/33/47)
        score = 0
        if check30: score += 20
        if check50: score += 33
        if check200: score += 47
        
        latest_days.append({
            "date": day.strftime('%d.%m.%Y'),
            "price_12h": round(df_12h.loc[day, 'price'] if day in df_12h.index else current_price, 2),
            "ma30_ok": "Ja" if check30 else "Nein",
            "ma50_ok": "Ja" if check50 else "Nein",
            "ma200_ok": "Ja" if check200 else "Nein",
            "rating": "KAUFEN" if score >= 70 else "Warten", # Schwellenwert 70%
            "score": score
        })

    # 5. Daten für Chart exportieren (kompletter Verlauf)
    chart_data = {
        "labels": df_daily.tail(365).index.strftime('%Y-%m-%d').tolist(),
        "prices": df_daily['price'].tail(365).round(2).tolist(),
        "ma30": df_daily['ma30'].tail(365).round(2).tolist(),
        "ma50": df_daily['ma50'].tail(365).round(2).tolist(),
        "ma200": df_daily['ma200'].tail(365).round(2).tolist(),
        "table": latest_days[::-1], # Neueste zuerst
        "last_update": datetime.now().strftime('%d.%m.%Y %H:%M')
    }
    
    with open('data.json', 'w') as f:
        json.dump(chart_data, f)

if __name__ == "__main__":
    fetch_bitcoin_data()