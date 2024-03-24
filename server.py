import os
import http.server
import socketserver
from operation_battleship_common_utilities import OpenAICaller


from http import HTTPStatus


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        msg = 'Hello! you requested %s' % (self.path)
        self.wfile.write(msg.encode())
        
        openAiCaller = OpenAICaller()
        msg2 = openAiCaller.get_completion("Write a short poem about Applications on Digial Ocean")
        self.wfile.write(msg2.encode())


port = int(os.getenv('PORT', 80))
print('Listening on port %s' % (port))
httpd = socketserver.TCPServer(('', port), Handler)
httpd.serve_forever()
