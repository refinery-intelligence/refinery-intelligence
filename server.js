const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8080;
const PUBLIC_DIR = path.join(__dirname, 'public');
const GATEWAY_LOG = path.join(__dirname, 'server.log');

const server = http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('X-Agent-Protocol', 'x402; version=1.4');

    // PAYWALL HANDSHAKE
    if (req.url === '/refinery_gate') {
        res.writeHead(402, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ 
            status: "Locked",
            asset_id: "REF-BUNDLE-MAY09",
            message: "XRP Ledger Transaction Required",
            instruction: "Submit TXID to /refinery_gate/verify"
        }));
        return;
    }

    // PUBLIC DISCOVERY
    let urlPath = req.url === '/' ? 'index.html' : req.url;
    let filePath = path.join(PUBLIC_DIR, urlPath);

    fs.readFile(filePath, (err, content) => {
        if (err) {
            res.writeHead(404);
            res.end('Asset Not Found');
            return;
        }
        res.writeHead(200);
        res.end(content);
    });
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`[LIVE] Refinery-01 Gateway: http://0.0.0.0:${PORT}`);
});
