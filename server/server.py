import socket
import time
import event



class Server(event.IOEvent):

    def __init__(self, ip, port, base):

        self.event_base = base
        self._get_listen_sock(ip, port)
        event.IOEvent.__init__(self, self.listen_sock.fileno(), event.IO_READ)
        self.no_authorization = {}
        self.online_users = {}
        self.rooms = {}

    def _get_listen_sock(self, ip_address, port):

        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_sock.bind((ip_address, port))
        self.listen_sock.listen(10)

    def _get_next_21game_time(self):

        half_time = 30 * 60
        now = time.time()
        next_21game_time = (int(now) / half_time + 1) * half_time
        return next_21game_time

    def read(self):

        conn, _ = self.listen_sock.accept()
        conn.setblocking(0)
        new_session = Session(conn, self.event_base, event.IO_READ)
        self.no_authorization[conn.fileno()] = new_session
        self.event_base.event_add(new_session)


class Session(event.IOEvent):

    def __init__(self, sock, base, io_type):

        self.sock = sock
        self.event_base = base
        self.user_id = -1
        event.IOEvent.__init__(self.sock.fileno(), io_type)
        self.authorization = False