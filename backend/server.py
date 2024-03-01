from flask import Flask, jsonify, render_template
from flask_cors import CORS
import requests
import numpy as np
import pandas as pd
from alpha_vantage.timeseries import TimeSeries

app = Flask(__name__)
CORS(app)  

API_KEY = "09I1ESM2FDLI0Y6D"
FEATURED_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "PYPL", "AMZN", "MCD", "NFLX",
    "AMD", "INTC", "CRM", "DIS", "BABA", "UBER", "SQ", "ADBE", "PEP",
    "JNJ", "V", "MA", "BAC", "WMT", "NVAX", "PG", "KO", "T", "INTU", "IBM", "NOW"
]

ts = TimeSeries(API_KEY, output_format='pandas')


@app.route('/')
def homepage():
    return render_template('index.html') 

@app.route('/portfolio/<user_id>')
def get_portfolio(user_id):
    DATABASE = {
        "user1": {"symbols": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "PYPL"]},
        "user2": {"symbols": ["AMZN", "MCD", "NFLX", "AMD", "INTC", "CRM"]},
        "user3": {"symbols": ["DIS", "BABA", "UBER", "SQ", "ADBE", "PEP"]},
        "user4": {"symbols": ["JNJ", "V", "MA", "BAC", "WMT", "NVAX"]},
        "user5": {"symbols": ["PG", "KO", "T", "INTU", "IBM", "NOW"]}
    }
    
    if user_id in DATABASE:
        symbols = DATABASE[user_id]["symbols"]
        weights = None
        total_portfolio_value = calculate_portfolio_value(symbols, weights)
        return jsonify({
            "user_id": user_id,
            "symbols": symbols,
            "total_portfolio_value": total_portfolio_value
        })
    else:
        return jsonify({"error_message": "User not found"}), 404

@app.route('/symbol/<symbol>')
def get_symbol_data(symbol):

    weekly_api_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol={symbol}&apikey={API_KEY}"
    global_quote_api_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    
    response = requests.get(weekly_api_url)
    if response.status_code == 200:
        symbol_data = response.json()
        if "Weekly Time Series" in symbol_data:
            last_refreshed = symbol_data["Meta Data"]["3. Last Refreshed"]
            latest_close_price = symbol_data["Weekly Time Series"][last_refreshed]["4. close"]
            return jsonify({
                "symbol": symbol,
                "last_refreshed": last_refreshed,
                "latest_close_price": latest_close_price
            })
        elif "Error Message" in symbol_data:
            return jsonify({"error_message": symbol_data["Error Message"]}), 400
    
    response = requests.get(global_quote_api_url)
    if response.status_code == 200:
        symbol_data = response.json()
        if "Global Quote" in symbol_data:
            latest_close_price = symbol_data["Global Quote"]["05. price"]
            last_refreshed = symbol_data["Global Quote"]["07. latest trading day"]
            return jsonify({
                "symbol": symbol,
                "last_refreshed": last_refreshed,
                "latest_close_price": latest_close_price
            })
        elif "Error Message" in symbol_data:
            return jsonify({"error_message": symbol_data["Error Message"]}), 400
    
    return jsonify({"error_message": "Failed to fetch data from Alpha Vantage API"}), 500

# Function to calculate portfolio value
def calculate_portfolio_value(symbols, weights=None):
    total_value = 0.0
    for symbol in symbols:
        latest_close_price = get_latest_close_price(symbol)
        if latest_close_price is not None:
            weight = weights[symbol] if weights and symbol in weights else 1.0 / len(symbols)
            total_value += latest_close_price * weight
    return total_value

# Function to fetch the latest close price of a symbol
def get_latest_close_price(symbol):
    global_quote_api_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(global_quote_api_url)
    if response.status_code == 200:
        symbol_data = response.json()
        if "Global Quote" in symbol_data:
            latest_close_price = float(symbol_data["Global Quote"]["05. price"])
            return latest_close_price
    return None

if __name__ == '__main__':
    app.run(debug=True)
