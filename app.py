# PYTHON RECEIPTS

import psycopg2
import glob
import os

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from funcs import *


app = Flask(__name__)
CORS(app)


@app.route('/api/cards', methods=['GET'])
def get_card_route():
    conn = psycopg2.connect(
        dbname=DBNAME,
        user=USER,
        password=PASSWORD,
        host="localhost",
        port=5432
    )
    
    cur = conn.cursor()
    cur.execute("SELECT name, price, image FROM pokemon")
    rows = cur.fetchall()
    
    cards = [
        {"name": row[0], "price": row[1], "image": row[2]}
        for row in rows
    ]
    
    cur.close()
    conn.close()
    
    return jsonify(cards)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/add-card', methods=['POST'])
def add_card_route():
    try:
        data = request.json
        name = data.get('name')
        set_name = data.get('set_name')
        rarity = data.get('rarity')
        
        if not all([name, set_name, rarity]):
            return jsonify({"error": "Missing required fields"}), 400
        
        card_data = search_card(name, set_name, rarity)
        print(card_data)
        
        if not card_data:
            return jsonify({"error": "Card not found"}), 404
        
        add_card(
            card_data["name"],
            card_data["set_name"],
            card_data["rarity"],
            card_data["price"],
            card_data["image"]
        )
        
        return jsonify({"success": True, "card": card_data}), 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    

@app.route('/api/remove-card', methods=['POST'])
def remove_card_route():
    try:
        data = request.json
        card_name = data.get('name')
        
        if not card_name:
            return jsonify({"error": "Card name is required"}), 400
        
        success = remove_card(card_name)
        
        if not success:
            return jsonify({"error": "Card not found in collection"}), 404
        
        return jsonify({"success": True, "message": "Card removed"}), 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/refresh-prices', methods=['POST'])
def refresh_prices():
    def background_refresh():
        refresh_all_prices()
    
    # Start in background thread
    thread = Thread(target=background_refresh)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "message": "Refresh started in background. Check Flask terminal for progress.",
        "updated": 0,
        "total": 84
    }), 200
    

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)