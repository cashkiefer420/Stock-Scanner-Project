import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(BASE_DIR, "..", "..", "static")
JSON_FOLDER = os.path.join(BASE_DIR, "..", "..", "json")
os.makedirs(JSON_FOLDER, exist_ok=True)

from flask import Flask, render_template, jsonify
import os
import json

app = Flask(__name__)

@app.route('/')
def index():
    with open(news_file_path, 'r') as file:
        articles = json.load(file)
    return render_template('News_display.html', articles=articles)

@app.route('/articles', methods=['GET'])
def get_articles():
    news_file_path = r'C:\Users\Carte\Documents\Stock-Scanner-Project-Windows\json\news.json'
    with open(news_file_path, 'r') as file:
        articles = json.load(file)
    return jsonify(articles)

if __name__ == '__main__':
    app.run(debug=True)
