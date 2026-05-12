import http.server
import socketserver
import os

PORT = 8081
DIRECTORY = "/Users/pablorufas/Documents/Claude/Scheduled"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
