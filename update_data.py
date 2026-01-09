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
    
    daily = df['price'].resample('D').last().to_frame()
    daily['ma30'] = daily['price'].rolling(30).mean()
    daily['ma50'] = daily['price'].rolling(50).mean()
    daily['ma200'] = daily['price'].rolling(200).mean()
    daily['rsi'] = calculate_rsi(daily['price'])
    daily = daily.dropna()

    invested_total = 0
    btc_accumulated = 0
    portfolio_values = []
    
    table_list = []
    for day, row in daily.iterrows():
        p, m30, m50, m200, rsi = row['price'], row['ma30'], row['ma50'], row['ma200'], row['rsi']
        score = (50 if p > m200 else 0) + (30 if p > m50 else 0) + (20 if rsi < 60 else 0)
        signal = "KAUFEN" if score >= 80 else "WARTEN"
        investment = 5.0 if signal == "KAUFEN" else 0.0
        
        if investment > 0:
            invested_total += investment
            btc_accumulated += (investment / p)
        
        portfolio_values.append(round(btc_accumulated * p, 2))
            
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
        "labels": daily.index.strftime('%d.%m').tolist(),
        "prices": daily['price'].round(2).tolist(),
        "ma30": daily['ma30'].round(2).tolist(),
        "ma50": daily['ma50'].round(2).tolist(),
        "ma200": daily['ma200'].round(2).tolist(),
        "portfolio_history": portfolio_values,
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
