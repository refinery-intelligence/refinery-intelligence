import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from vault.payments.usdc.verify_polygon_rpc_tx import verify_transaction
from vault.payments.usdc.verifier import create_payment_request
from vault.payments.usdc.check_access import check_access
from vault.payments.usdc.serve_bundle import serve_bundle

class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/payments/usdc/request":
            qs = parse_qs(parsed.query)
            bundle_id = qs.get("bundle_id", [None])[0]
            buyer_id = qs.get("buyer_id", ["anonymous"])[0]

            if not bundle_id:
                return self._send_json({
                    "error": "missing_bundle_id",
                    "usage": "/payments/usdc/request?bundle_id=xrp-etf-temporal-intel-v1"
                }, 400)

            try:
                request = create_payment_request(bundle_id, buyer_id)
                return self._send_json(request)
            except Exception as e:
                return self._send_json({
                    "error": "payment_request_failed",
                    "detail": str(e)
                }, 400)

        if parsed.path == "/payments/usdc/access":
            qs = parse_qs(parsed.query)
            request_id = qs.get("request_id", [None])[0]

            if not request_id:
                return self._send_json({
                    "error": "missing_request_id",
                    "usage": "/payments/usdc/access?request_id=REQUEST_ID"
                }, 400)

            result = check_access(request_id)
            return self._send_json(result)
        if parsed.path == "/payments/usdc/bundle":
            qs = parse_qs(parsed.query)
            request_id = qs.get("request_id", [None])[0]

            if not request_id:
                return self._send_json({
                    "error": "missing_request_id",
                    "usage": "/payments/usdc/bundle?request_id=REQUEST_ID"
                }, 400)

            result = serve_bundle(request_id)
            return self._send_json(result)
        if parsed.path == "/payments/usdc/verify":
            qs = parse_qs(parsed.query)

            request_id = qs.get("request_id", [None])[0]
            tx_hash = qs.get("tx_hash", [None])[0]

            if not request_id or not tx_hash:
                return self._send_json({
                    "error": "missing_required_params",
                    "usage": "/payments/usdc/verify?request_id=REQUEST_ID&tx_hash=TX_HASH"
                }, 400)

            try:
                result = verify_transaction(
                    request_id,
                    tx_hash
                )

                return self._send_json(result)

            except Exception as e:
                return self._send_json({
                    "error": "verification_exception",
                    "detail": str(e)
                }, 500)
        return self._send_json({"error": "not_found"}, 404)

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8787), Handler)
    print("Refinery payment API running on http://127.0.0.1:8787")
    server.serve_forever()
