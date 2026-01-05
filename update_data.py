import requests
import pandas as pd
import json
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
    
    # Indikatoren
    daily = df['price'].resample('D').last().to_frame()
    daily['ma50'] = daily['price'].rolling(50).mean()
    daily['ma200'] = daily['price'].rolling(200).mean()
    daily['rsi'] = calculate_rsi(daily['price'])
    daily = daily.dropna()

    # Backtesting & 5€ Strategie
    invested_total = 0
    btc_accumulated = 0
    
    table_list = []
    for day, row in daily.iterrows():
        p, m50, m200, rsi = row['price'], row['ma50'], row['ma200'], row['rsi']
        
        # Deine Logik: KAUFEN nur bei hohem Score
        score = (50 if p > m200 else 0) + (30 if p > m50 else 0) + (20 if rsi < 60 else 0)
        
        # Signal: 5€ oder 0€
        signal = "KAUFEN" if score >= 80 else "WARTEN"
        investment = 5.0 if signal == "KAUFEN" else 0.0
        
        # Simulation
        if investment > 0:
            invested_total += investment
            btc_accumulated += (investment / p)
            
        table_list.append({
            "date": day.strftime('%d.%m.%Y'),
            "price": round(float(p), 2),
            "rsi": round(float(rsi), 1),
            "score": int(score),
            "signal": signal,
            "invest_today": f"{investment:.2f} €"
        })

    current_val = btc_accumulated * daily['price'].iloc[-1]
    perf = ((current_val / invested_total) - 1) * 100 if invested_total > 0 else 0

    output = {
        "labels": daily.tail(30).index.strftime('%d.%m').tolist(),
        "prices": daily['price'].tail(30).round(2).tolist(),
        "table": table_list[::-1][:10],
        "backtest": {
            "invested": round(invested_total, 2),
            "current_value": round(current_val, 2),
            "performance": round(perf, 1)
        },
        "last_update": datetime.now().strftime('%d.%m.%Y %H:%M')
    }
    
    with open('data.json', 'w') as f:
        json.dump(output, f)

if __name__ == "__main__":
    fetch_bitcoin_data()
