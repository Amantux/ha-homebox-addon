
import os
import sqlite3

from flask import Flask, jsonify, request

app = Flask(__name__)
DB_PATH = os.environ.get('HOMEBOX_DB_PATH', '/data/homebox.db')

def search_homebox(query):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, description FROM items WHERE name LIKE ? OR description LIKE ?",
                       (f'%{query}%', f'%{query}%'))
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        return [("Error", str(e))]

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "No query provided"}), 400
    results = search_homebox(query)
    return jsonify([{"name": r[0], "description": r[1]} for r in results])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
