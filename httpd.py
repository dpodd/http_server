import socket
from optparse import OptionParser
from icecream import ic
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import logging
from connection import Connection


def parse_headers(raw_headers):
    headers = raw_headers.split(b'\r\n')
    ic("in parse_headers", headers)
    return headers


class Request:
    def __init__(self, raw_request):
        self.raw = raw_request

    @property
    def headers(self):
        return {h[:h.find(b':')].decode(): h[h.find(b':'):].decode() for h in self.parse_headers()}

    def parse_headers(self):
        return self.raw.split(b'\r\n')[1:]



def http_handler(conn):
    CRLFx2 = b'\r\n\r\n'
    with conn:
        while True:
            try:
                ic('Waiting for new request')
                buff = conn.recv(1024)
                print(buff)
                if not buff: break  # client closed socket
                if CRLFx2 not in buff:
                    raise NotImplementedError("Invalid request: no CRLF delimiter")

                pos = buff.find(CRLFx2)
                raw_req = buff[:pos]  # server assumes the request has no body

                ic('hello')
                request = Request(raw_req)
                ic(request.headers)
                # conn.sendall(b'HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n')
                # conn.close() # closing socket, implementing short-lived connection server
                # conn.sendall(b'')

                # raw_req = headers


            except NotImplementedError as e:
                logging.exception(f"An error occurred with this message: {e}")
                break
            except socket.timeout:
                logging.info('Timeout error. Closing the socket...')
                break


if __name__ == '__main__':
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=40000)
    op.add_option("--host", action="store", type=str, default='localhost')
    op.add_option("-w", "--workers", action="store", type=int, default=5)
    opts, args = op.parse_args()

    logging.basicConfig(level=logging.INFO)
    logging.info(f"Server is running on host '{opts.host}' and port {opts.port}")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((opts.host, opts.port))
    s.listen(5)

    stdout_lock = Lock()

    while True:
        try:
            logging.info("Server is ready to accept connection...")
            conn, addr = s.accept()
            conn.settimeout(10)
            #connection = Connection(conn)
            with ThreadPoolExecutor(max_workers=5) as executor:
                executor.submit(http_handler, conn)
                #t = Thread(target=http_handler, args=(conn, ))

        except Exception as e:
            logging.info("Error! Details: %s" % e)
        break

    logging.info("closing server....")
    s.close()
