import unittest
import json
from flask import Flask
from blueprint.Stock_search_up import app, load_stocks, get_stock_metrics

class StockSearchTestCase(unittest.TestCase):
    def setUp(self):
        # Set up the Flask test client
        self.app = app.test_client()
        self.app.testing = True

    def test_index(self):
        # Test the index route
        result = self.app.get('/')
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'Look.html', result.data)

    def test_get_stock_no_query(self):
        # Test the /Fetch_data_ticker route with no query
        result = self.app.get('/Fetch_data_ticker')
        self.assertEqual(result.status_code, 400)
        data = json.loads(result.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "No query provided")

    def test_get_stock_valid_query(self):
        # Test the /Fetch_data_ticker route with a valid query
        sample_query = "AAPL"
        result = self.app.get(f'/Fetch_data_ticker?query={sample_query}')
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertIsInstance(data, dict)
        self.assertIn("Ticker", data)
        self.assertEqual(data["Ticker"], sample_query)

    def test_load_stocks(self):
        # Test the load_stocks function
        filepath = 'path_to_your_test_json_file.json'  # Replace with the path to your test JSON file
        stocks = load_stocks(filepath)
        self.assertIsInstance(stocks, list)

    def test_get_stock_metrics(self):
        # Test the get_stock_metrics function
        sample_query = "AAPL"
        filepath = 'path_to_your_test_json_file.json'  # Replace with the path to your test JSON file
        stock_metrics = get_stock_metrics(sample_query, filepath)
        self.assertIsInstance(stock_metrics, dict)
        self.assertIn("Ticker", stock_metrics)
        self.assertEqual(stock_metrics["Ticker"], sample_query)

if __name__ == '__main__':
    unittest.main()
