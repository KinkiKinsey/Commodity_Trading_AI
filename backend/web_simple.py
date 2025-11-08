from http.server import SimpleHTTPRequestHandler, HTTPServer
import json

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "backend is running", "message": "RingShell API Server"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"message": "RingShell Backend", "path": self.path}
            self.wfile.write(json.dumps(response).encode())

if __name__ == '__main__':
    print("Starting backend server on http://0.0.0.0:8000")
    server = HTTPServer(('0.0.0.0', 8000), Handler)
    server.serve_forever()
