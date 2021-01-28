import socket
from optparse import OptionParser
from icecream import ic
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import logging
from connection import Connection


def http_handler(conn, addr):
    with stdout_lock:
        print(f"New connection with {addr}")
    CRLFx2 = b'\r\n\r\n'
    with conn:
        buff = b''
        old_buffer_remainder = b''
        raw_req = b''
        while True:
            try:
                ic('Waiting for new request')
                buff = conn.recv(1024)
                buff = old_buffer_remainder + buff
                print(buff)
                print('LENGTH', len(buff))
                if not buff: break # client closed socket
                if CRLFx2 not in buff:
                    raw_req += buff # for long requests - adding data to the request. not tested
                    buff = b''
                while buff:
                    if CRLFx2 in buff:
                        pos = buff.find(CRLFx2)
                        msg_len = pos + len(CRLFx2)
                        raw_headers += buff[:msg_len] # case 1: no content-length
                        # TODO: send request to requests handler Request(req)
                        request =
                        # now parse headers and find Content-Length header
                        parse_headers()
                        # conn.sendall(b'HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n')

                        # conn.close() # closing socket, implementing short-lived connection server
                        # conn.sendall(b'')
                        print("REQUEST END FOUND. Request: ", req, sep='\n')
                        print(buff)
                        buff = buff[msg_len:]
                        ic("new buffer:", buff)
                    else:
                        old_buffer_remainder = buff
                        buff = b''

            # except RuntimeError:
            #     break
            except socket.timeout:
                logging.info('Timeout error. Closing the socket...')
                break


if __name__ == '__main__':
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=40000)
    op.add_option("--host", action="store", type=str, default='localhost')
    op.add_option("-w", "--workers", action="store", type=int, default=5)
    opts, args = op.parse_args()

    print(f"Server is running on host '{opts.host}' and port {opts.port}")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((opts.host, opts.port))
    s.listen(5)

    stdout_lock = Lock()

    while True:
        try:
            print("Server is ready to accept connection...")
            conn, addr = s.accept()
            conn.settimeout(10)
            #connection = Connection(conn)
            with ThreadPoolExecutor(max_workers=5) as executor:
                executor.submit(http_handler, conn, addr)
                #t = Thread(target=http_handler, args=(conn, addr))

        except Exception as e:
            print("Error! Details: %s" % e)
        break

    print("closing server....")
    s.close()
