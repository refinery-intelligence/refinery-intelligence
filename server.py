from flask import Flask, send_from_directory, jsonify, make_response
import os

app = Flask(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
VAULT_DIR = os.path.join(BASE_DIR, 'vault')

@app.after_request
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['X-Agent-Protocol'] = 'x402; version=1.4.1'
    return response

@app.route('/')
def index():
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory(PUBLIC_DIR, 'manifest.json')

@app.route('/specs.json')
def specs():
    return send_from_directory(PUBLIC_DIR, 'specs.json')

@app.route('/refinery_gate')
def gatekeeper():
    # The 402 Payment Required handshake
    content = {
        "status": "LOCKED",
        "asset_id": "REF-BUNDLE-MAY09",
        "price": "XRP_MICROTRANSACTION",
        "instruction": "Transmit TXID to /refinery_gate/verify for vault access."
    }
    return make_response(jsonify(content), 402)

@app.errorhandler(404)
def not_found(e):
    return "Asset Not Found", 404

if __name__ == '__main__':
    print("--- REFINERY-01 HOBART NODE ACTIVE ---")
    app.run(host='0.0.0.0', port=8080)
