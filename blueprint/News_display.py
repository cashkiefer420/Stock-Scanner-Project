from flask import Flask, render_template, jsonify
import os
import json

app = Flask(__name__)

@app.route('/')
def index():
    news_file_path = r'/home/ec2-user/Stock-Scanner-Project'
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
