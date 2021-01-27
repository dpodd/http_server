import socket
from optparse import OptionParser
from icecream import ic
from threading import Thread, Lock
import logging
from connection import Connection

if __name__ == '__main__':
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=40000)
    op.add_option("--host", action="store", type=str, default='localhost')
    opts, args = op.parse_args()

    print(f"Server is running on host '{opts.host}' and port {opts.port}")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((opts.host, opts.port))
    s.listen(5)

    stdout_lock = Lock()

    def http_handler(conn, addr):
        with stdout_lock:
            print(f"New connection with {addr}")

        while True:

            try:
                data = conn.receive()
                print(data)
            except RuntimeError:
                break
            except socket.timeout:
                logging.info('Timeout error. Closing the socket...')
                break
            with stdout_lock:
                print("DATA: ", data)

        conn.sock.close()

    threads = []
    while True:
        try:
            print("Server ready to accept...")
            conn, addr = s.accept()
            conn.settimeout(10)
            connection = Connection(conn)
            t = Thread(target=http_handler, args=(connection, addr))
            threads.append(t)
            t.start()
        except Exception as e:
            print("Error! Details: %s" % e)
        break

    for t in threads:
        t.join()

    print("closing connection....")
    s.close()
