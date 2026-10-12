#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8089
AUTH_TOKEN = "zlf-idn-task-sync-2026"
COOKIE_PATH = "/home/zulfi/Projects/task_idn_cookie.json"

class CookieSyncHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Auth-Token")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/status" or self.path == "/":
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            cookie_exists = os.path.exists(COOKIE_PATH)
            last_updated = None
            cookie_names = []
            
            if cookie_exists:
                try:
                    with open(COOKIE_PATH, "r") as f:
                        data = json.load(f)
                        last_updated = data.get("updated_at")
                        cookies_list = data.get("cookies", [])
                        cookie_names = [c.get("name") for c in cookies_list if isinstance(c, dict)]
                except Exception as e:
                    last_updated = f"Error reading: {e}"

            status_payload = {
                "status": "online",
                "service": "task-cookie-receiver",
                "cookie_file_exists": cookie_exists,
                "last_updated": last_updated,
                "detected_cookies": cookie_names
            }
            self.wfile.write(json.dumps(status_payload, indent=2).encode("utf-8"))
        else:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()

    def do_POST(self):
        if self.path != "/api/sync-cookie":
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()
            return

        token = self.headers.get("X-Auth-Token")
        if token != AUTH_TOKEN:
            self.send_response(403)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Forbidden: Invalid auth token"}).encode("utf-8"))
            return

        try:
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len)
            data = json.loads(body.decode("utf-8"))

            if not isinstance(data, dict):
                raise ValueError("Payload must be a JSON object")

            # Enrich with received timestamp
            data["server_received_at"] = datetime.now().isoformat()

            with open(COOKIE_PATH, "w") as f:
                json.dump(data, f, indent=2)

            try:
                os.chmod(COOKIE_PATH, 0o666)
            except Exception:
                pass

            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response_payload = {
                "status": "success",
                "message": "Cookie successfully saved on deb-zlf!",
                "saved_at": data["server_received_at"],
                "cookie_count": len(data.get("cookies", []))
            }
            self.wfile.write(json.dumps(response_payload).encode("utf-8"))
            print(f"[{datetime.now().isoformat()}] Cookie synced successfully. Cookies count: {len(data.get('cookies', []))}", flush=True)

        except Exception as e:
            self.send_response(400)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Failed to parse payload: {str(e)}"}).encode("utf-8"))

if __name__ == "__main__":
    print(f"Starting Task Cookie Receiver on 0.0.0.0:{PORT}...", flush=True)
    server = HTTPServer(("0.0.0.0", PORT), CookieSyncHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
