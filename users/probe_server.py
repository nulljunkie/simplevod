import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class ProbeState:
    liveness = True
    readiness = False

class ProbeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            if ProbeState.liveness:
                self.send_response(200)
            else:
                self.send_response(500)
            self.end_headers()
            self.wfile.write(b"OK" if ProbeState.liveness else b"NOT OK")
        elif self.path == "/readyz":
            if ProbeState.readiness:
                self.send_response(200)
            else:
                self.send_response(500)
            self.end_headers()
            self.wfile.write(b"OK" if ProbeState.readiness else b"NOT READY")
        else:
            self.send_response(404)
            self.end_headers()

def start_probe_server(port=8084):
    server = HTTPServer(("", port), ProbeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server 
