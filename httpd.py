import socket
import os
from optparse import OptionParser
from icecream import ic
from concurrent.futures import ThreadPoolExecutor
import logging

CRLFx2 = b'\r\n\r\n'


class RequestHandler:
    @classmethod
    def get_response(cls, request, _dir):
        response = cls(request, _dir)
        response.process_request()
        return response.to_binary() # TODO ??? Refactor?

    def __init__(self, request, _dir):
        self.request = request
        self.dir = _dir

    def process_request(self):
        # 1 process resourse
        path_to_file = self.get_path(self.request.path)
        # 2 process METHOD GET/HEAD

    def get_path(self, path):


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

    def process(self, conn, _dir):
        with conn:
            while True:
                try:
                    ic('Waiting for new request')
                    buff = conn.recv(1024) # TODO move to consts
                    print(buff)
                    if not buff: break  # if client closed socket
                    if CRLFx2 not in buff:
                        # send 500 invalid request?  # TODO refactor this code, make standard implementation
                        raise NotImplementedError("Unsupported request: no CRLF delimiter")

                    pos = buff.find(CRLFx2) + len(CRLFx2) # TODO Remove?
                    raw_req = buff[:pos]  # server throws out the body of the request if it exists

                    request = Request(raw_req)
                    ic(request.headers)
                    ic(request.method)
                    # try:
                    #     response = RequestHandler.get_response(request, _dir)
                    # except:
                    #     pass

                    # conn.sendall(response)

                except NotImplementedError as e:
                    logging.exception(f"An error occurred; the message is: {e}")
                    break
                except socket.timeout:
                    logging.exception('Timeout error. Closing the socket...')
                    break


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
