
import socket
import time
import event

class Server(object):

    def __init__(self, ip, port):

        self.listen_sock = self._get_listen_sock(ip, port)
        self.reactor = event.EventBase()
        self.online_users = {}
        self.rooms = {}


    def _get_listen_sock(self, ip, port):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((ip, port))
        sock.listen(10)

    def _get_next_21game_time(self):

        half_time = 30 * 60
        now = time.time()
        next_21game_time = (int(now) / half_time + 1) * half_time
        return next_21game_time


class RoomInfo(object):
    pass


class UserInfo(object):
    pass

