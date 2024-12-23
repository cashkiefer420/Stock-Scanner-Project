import yfinance as yf
import json
from datetime import datetime, timedelta
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event

current_dir = os.path.dirname(os.path.abspath(__file__))

while os.path.basename(current_dir) != "Stock-Scanner-Project":
    current_dir = os.path.dirname(current_dir)
    if current_dir == "/":
        raise FileNotFoundError("Base directory 'Stock-Scanner-Project' not found!")

base_dir = current_dir

# Define the absolute path to the JSON file
TICKER_FILE_PATH = ./Stock-Scanner-Project/json/Sample_tickers.json
EXPORT_FILE_PATH = ./Stock-Scanner-Project/json/stock_data_export.json

with open(TICKER_FILE_PATH, 'r') as file:
    content = file.read()
    print(content)
