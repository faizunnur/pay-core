#!/usr/bin/env python3
"""A deliberately slow stand-in for the shared rules service.

Week 2, Canary A. PayCore's risk engine calls RULES_SERVICE_URL with a 250 ms
timeout (RISK_ENGINE_TIMEOUT_MS). This stub sleeps for longer than that, so every
payment waits the full timeout, logs a warning, and scores locally instead.

The result: no errors, no failed requests, and every payment ~250 ms slower.
That is what a slow dependency looks like from the outside.
"""
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DELAY_SECONDS = float(os.getenv("RULES_STUB_DELAY", "2.0"))
PORT = int(os.getenv("RULES_STUB_PORT", "8080"))


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        if length:
            self.rfile.read(length)
        time.sleep(DELAY_SECONDS)
        body = json.dumps({"score": 0}).encode()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # The caller already gave up at its 250 ms timeout. That is the point.
            pass

    def do_GET(self) -> None:
        body = b'{"status":"ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:
        pass


if __name__ == "__main__":
    print(f"rules-stub listening on :{PORT}, sleeping {DELAY_SECONDS}s per call", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
