import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import mimetypes
import pathlib
import socket
from threading import Thread
from datetime import datetime
import urllib.parse


BASE_DIR = pathlib.Path()
BUFFER_NEW_LOCATION = 302
BUFFER_ALL_OK = 200
BUFFER_ERROR = 400
BUFFER = 1024
PORT_HTTP = 3000
PORT_SOCKET = 5000
IP_SOCKET = '127.0.0.1'


def send_data_to_socket(data):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(data, (IP_SOCKET, PORT_SOCKET))
    client_socket.close()


class HttpGetHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        send_data_to_socket(data)
        self.send_response(BUFFER_NEW_LOCATION)
        self.send_header('Location', '/index.html')
        self.end_headers()

    def do_GET(self):
        pg_url = urllib.parse.urlparse(self.path)

        match pg_url.path:
            case '/':
                self.send_html_file('index.html')
            case '/message':
                self.send_html_file('message.html')
            case _:
                file = BASE_DIR.joinpath(pg_url.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html_file('error.html', BUFFER_ERROR)
    
    def send_html_file(self, filename, status=BUFFER_ALL_OK):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())      

    def send_static(self, filename):
        self.send_response(BUFFER_ALL_OK)
        # mt, *rest = mimetypes.guess_type(filename)
        mt = mimetypes.guess_type(filename)
        if mt:
            # self.send_header("Content-Type", mt)
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())       


def save_data(data):
    try:
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_parse = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        data_post = {datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"): data_parse}
        with open(BASE_DIR.joinpath('storage\data.json'), 'a', encoding='utf-8') as file:
            json.dump(data_post, file, ensure_ascii=False)
            file.write("\n")
    except ValueError as err:
        logging.error(f'Failed parse data {data_parse} with error {err}')
    except OSError as err:
        logging.error(f'Failed write data {data_parse} with error {err}')


def run(server_class=HTTPServer, handler_class=HttpGetHandler):
    server_address = ('', PORT_HTTP)
    http_server = server_class(server_address, handler_class)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def run_socket_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)
    try:
        while True:
            # data, address = server_socket.recv(BUFFER)
            data = server_socket.recv(BUFFER)
            save_data(data)
    except KeyboardInterrupt:
        logging.info('Socket server stoped')
    finally:
        server_socket.close()


if __name__=='__main__':
    logging.basicConfig(level=logging.INFO, format='%(TreadName)s %(message)s')
    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket = Thread(target=run_socket_server, args=(IP_SOCKET, PORT_SOCKET))
    thread_socket.start()
    