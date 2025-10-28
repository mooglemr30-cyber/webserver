#!/usr/bin/env python3
from flask import Flask

app = Flask(__name__)

@app.route('/test')
def test():
    return {'status': 'ok'}

if __name__ == '__main__':
    print("Starting minimal Flask server on port 8001...")
    app.run(host='0.0.0.0', port=8001, debug=False)
