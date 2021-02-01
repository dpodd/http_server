import socket
import os
from optparse import OptionParser
from icecream import ic
from concurrent.futures import ThreadPoolExecutor
import logging

CRLFx2 = b'\r\n\r\n'
MAX_MSG_LEN = 2048
MSG_LEN = 1024
OK = 200
Forbidden = 403
NotFound = 404
NotAllowed = 405
phrases = {
    OK: 'OK',
    Forbidden: 'Forbidden',
    NotFound: 'Not Found',
    NotAllowed: 'Not Allowed',
}


class RequestHandler:
    @classmethod
    def get_response(cls, request, _dir):
        response = cls(request, _dir)
        resp = response.process_request()
        return resp

    def __init__(self, request, _dir):
        self.request = request
        self.dir = _dir
        self.content = None

    def process_request(self):
        path_to_file = self.get_path(self.request.path)
        if self.request.method == 'GET':
            self.content, code = self.get_content(path_to_file)
            response = self.build_response(code)
        elif self.request.method == 'HEAD':
            self.content = b''
            response = self.build_response(OK)
        else:
            self.content = b''
            response = self.build_response(NotAllowed)

        return response

    def get_path(self, path):
        if path == '/':
            return os.path.join(os.path.abspath('.'), self.dir, 'index.html')
        return os.path.join(os.path.abspath('.'), self.dir, path)

    @staticmethod
    def get_content(path_to_file):
        try:
            with open(path_to_file, 'rb') as file:
                content = file.read()
                return content, OK
        except Exception as e: # TODO add exceptions to 403, 404 error
            ic("Error: ", e)
            return b'', NotFound

    def set_headers(self):


    def build_response(self, code):
        status_line = f"HTTP/1.0 {code} {phrases[code]}"
        status_line = status_line.encode() + b'\r\n'
        content_length_header = 'Content-Length: ' + '%s' % len(self.content)
        content_length_header = content_length_header.encode()

        return status_line + content_length_header + CRLFx2 + self.content

    def to_binary(self):
        pass


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
                    ic('Waiting for new request')
                    buff = conn.recv(MSG_LEN)
                    print(buff)
                    ic(len(buff))
                    if not buff: break  # if client closed socket
                    chunks.append(buff)
                    bytes_recd = bytes_recd + len(buff)
                    if CRLFx2 in buff: break
                except socket.timeout:
                    logging.exception('Timeout error. Closing the connection...')
                    break
            raw_req = b''.join(chunks)
            ic(raw_req)
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
                conn.settimeout(10) # TODO ADD TO CONSTS
                with ThreadPoolExecutor(max_workers=5) as executor: # TODO max_workers
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
        logging.error("Server has been crashed %s" % e) # TODO add msg
