import socket
import os
import errno
from optparse import OptionParser
from urllib.parse import unquote
from icecream import ic # TODO remove
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
from concurrent.futures import ThreadPoolExecutor
import logging
from htmlgen import create_index_page_if_not_exist

CRLFx2 = b'\r\n\r\n'
MAX_MSG_LEN = 2048
MSG_LEN = 1024
TIMEOUT = 10
OK = 200
Forbidden = 403
NotFound = 404
NotAllowed = 405
InternalServerError = 500
phrases = {
    OK: 'OK',
    Forbidden: 'Forbidden',
    NotFound: 'Not Found',
    NotAllowed: 'Not Allowed',
    InternalServerError: "Internal Server Error"
}
SERVER_NAME = 'Server-X'


class RequestHandler:
    content_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "css": "text/css",
        "html": "text/html",
        "js": "application/javascript",
        "swf": "application/x-shockwave-flash",
    }

    @classmethod
    def get_response(cls, request, _dir):
        response = cls(request, _dir)
        response_binary = response.process_request()
        return response_binary

    def __init__(self, request, _dir):
        self.request = request
        self.dir = _dir
        self.content = None
        self.code = None
        self.content_length = None
        self.content_type = None
        self.headers = {}

    def process_request(self):
        path_to_file = unquote(self.get_path(self.request.path))
        if self.request.method == 'GET':
            create_index_page_if_not_exist(path_to_file)
            self.content, self.code, self.content_length = self.get_content(path_to_file, open_file=True)
            response = self.build_response()
        elif self.request.method == 'HEAD':
            self.content, self.code, self.content_length = self.get_content(path_to_file, open_file=False)
            response = self.build_response()
        else:
            self.content = b''
            self.code = NotAllowed
            response = self.build_response()
        return response

    def get_path(self, path):
        if path.startswith('/'):
            path = path[1:]
        path_to_resource = os.path.join(os.path.abspath('.'), self.dir, path)
        if os.path.isdir(path_to_resource):
            return os.path.join(path_to_resource, 'index.html')
        return os.path.join(path_to_resource)

    def get_content(self, path_to_file, open_file=False):
        try:
            with open(path_to_file, 'rb') as file:
                if open_file:
                    content = file.read()
                    content_length = len(content)
                    self.set_content_type(path_to_file)
                else:
                    line = file.readline()
                    content = b''
                    content_length = os.path.getsize(path_to_file)
                    self.set_content_type(path_to_file)
                return content, OK, content_length
        except IOError as e:
            if e.errno == errno.ENOENT:
                return b'', NotFound, None
            elif e.errno == errno.EACCES:
                return b'', Forbidden, None
        except Exception as e:
            logging.error(e)
            return b'', InternalServerError, None

    def set_content_type(self, path_to_file):
        _, ext = os.path.splitext(path_to_file)
        ext = ext[1:]  # remove dot
        if ext in self.content_types.keys():
            self.content_type = self.content_types.get(ext)

    def set_headers(self):
        now = datetime.now()
        stamp = mktime(now.timetuple())

        self.headers.update({
            'Date': format_date_time(stamp),
            'Server': SERVER_NAME,
            'Connection': 'closed'  # short-lived connections server
        })

        if self.request.method in ['GET', 'HEAD']:
            if self.content_length:
                self.headers.update({'Content-Length': self.content_length})

            if self.content_type:
                self.headers.update({'Content-Type': self.content_type})

    def build_response(self):
        self.set_headers()
        status_line = f"HTTP/1.1 {self.code} {phrases[self.code]}"
        status_line = status_line.encode() + b'\r\n'

        headers = [status_line]
        for k, v in self.headers.items():
            header = f"{k}: {v}".encode() + b'\r\n'
            headers.append(header)
        headers_together = b''
        for h in headers:
            headers_together += h
        return headers_together + b'\r\n' + self.content


class Request:
    def __init__(self, raw_request):
        self.raw = raw_request
        self.lines = [item.decode() for item in self.raw.split(b'\r\n') if item]
        self.headers = self.get_headers()
        self.method = self.get_method()
        self.path = self.get_path()

    def get_headers(self):
        lines = self.lines[1:]  # throw away the start line
        return {l[:l.find(':')]: l[l.find(':')+1:].strip() for l in lines}

    def get_method(self):
        return self.lines[0].split()[0]

    def get_path(self):
        return self.lines[0].split()[1]


class Worker:
    def __call__(self, conn, _dir):
        self.process(conn, _dir)

    @staticmethod
    def process(conn, _dir):
        with conn:
            chunks = []
            bytes_recd = 0
            while bytes_recd < MAX_MSG_LEN:
                try:
                    buff = conn.recv(MSG_LEN)
                    print(buff) # TODO
                    if not buff: break  # if client closed socket
                    chunks.append(buff)
                    bytes_recd = bytes_recd + len(buff)
                    if CRLFx2 in buff: break
                except socket.timeout:
                    logging.exception('Timeout error. Closing the connection...')
                    break
            raw_req = b''.join(chunks)
            request = Request(raw_req)
            response = RequestHandler.get_response(request, _dir)
            conn.sendall(response)


class Server:
    def __init__(self, host, port, max_workers, root_directory):
        self.socket = None
        self.host = host
        self.port = port
        self.max_workers = max_workers
        self.root_directory = root_directory
        self._check_root_dir()

    def _check_root_dir(self):
        _dir = os.path.abspath('.')
        _dir = os.path.join(_dir, self.root_directory)
        if not os.path.exists(_dir):
            raise NotADirectoryError(f"Path not found: {_dir}")

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen()

        logging.info("Server is ready to accept connections...")
        while True:
            try:
                conn, addr = self.socket.accept()
                conn.settimeout(TIMEOUT)
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    executor.submit(Worker(), conn, self.root_directory)
            except Exception as e:
                logging.info("Error during handling request. Details: %s" % e)
            break  # TODO : delete after debug


if __name__ == '__main__':
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=40000)
    op.add_option("--host", action="store", type=str, default='localhost')
    op.add_option("-w", "--workers", action="store", type=int, default=5)
    op.add_option("-r", "--root_dir", action="store", type=str, default='/') # TODO turn to Arg? HARDCODED!
    opts, args = op.parse_args()

    logging.basicConfig(level=logging.INFO)
    logging.info(f"Server is running on host '{opts.host}' and port {opts.port}")

    try:
        server = Server(opts.host, opts.port, opts.workers, opts.root_dir)
    except NotADirectoryError as e:
        logging.error("Cannot start server: %s" % e)
        raise

    try:
        server.start()
    except KeyboardInterrupt:
        logging.info("Server has been stopped by admin")
    except Exception as e:
        logging.error("Server has been crashed %s" % e)
