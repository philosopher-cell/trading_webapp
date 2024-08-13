import os
from flask import Flask, jsonify
import pandas as pd
import time
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

# Binance Testnet API credentials
API_KEY = os.environ.get('BINANCE_API_KEY')
API_SECRET = os.environ.get('BINANCE_API_SECRET')

# Set up Binance client
client = Client(os.environ.get('API_KEY'), os.environ.get('API_SECRET'), testnet=True)

# Define the trading parameters
symbol = 'BTCUSDT'
trade_amount = 0.001  # Define the amount of BTC you want to trade
buy_price = None
sell_price = None

def get_current_price():
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except Exception as e:
        print(f"Error fetching current price: {e}")
        return None

def place_buy_order(price, amount):
    try:
        order = client.order_limit_buy(
            symbol=symbol,
            quantity=amount,
            price='{:.8f}'.format(price)
        )
        return order
    except Exception as e:
        print(f"Error placing buy order: {e}")
        return None

def place_sell_order(price, amount):
    try:
        order = client.order_limit_sell(
            symbol=symbol,
            quantity=amount,
            price='{:.8f}'.format(price)
        )
        return order
    except Exception as e:
        print(f"Error placing sell order: {e}")
        return None

def calculate_drawdown(current_price, buy_price):
    if buy_price is None:
        return 0
    return (buy_price - current_price) * trade_amount

@app.route('/api/trade')
def trade():
    global buy_price, sell_price

    current_price = get_current_price()
    if current_price is None:
        return jsonify({"message": "Error fetching current price", "drawdown": 0})

    drawdown = calculate_drawdown(current_price, buy_price)

    if buy_price is None and sell_price is None:
        # Initial buy order
        buy_order = place_buy_order(current_price, trade_amount)
        if buy_order:
            buy_price = current_price
            return jsonify({"message": f"Placed buy order at {buy_price}", "drawdown": drawdown})

    elif buy_price is not None and current_price > buy_price:
        # Place sell order if current price is higher than buy price
        sell_order = place_sell_order(current_price, trade_amount)
        if sell_order:
            sell_price = current_price
            buy_price = None
            return jsonify({"message": f"Placed sell order at {sell_price}", "drawdown": 0})

    elif sell_price is not None and current_price < sell_price:
        # Place buy order if current price is lower than sell price
        buy_order = place_buy_order(current_price, trade_amount)
        if buy_order:
            buy_price = current_price
            sell_price = None
            return jsonify({"message": f"Placed buy order at {buy_price}", "drawdown": 0})

    return jsonify({"message": f"Current price: {current_price}", "drawdown": drawdown})

if __name__ == '__main__':
    app.run(debug=False)
