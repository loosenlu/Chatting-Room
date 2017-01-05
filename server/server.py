
import socket
<<<<<<< HEAD
import event



class UserInfo(object):

    def __init__(self):
        self.user_id = id
        self.user_name = name





class Server(object):


    def __init__(self, ip_address, port):

        self.reactor = event.EventBase()
        self.listen_sock = self._get_listen_sock(ip_address, port)



    def _get_listen_sock(self, ip_address, port):
        """Make a listen socket(ip_address, port).

        """
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(ip_address, int(port))
        server_sock.listen(10)

    def _check_time(self):
        pass
=======
import time
import event

class Server(object):

    def __init__(self, ip, port):

        self.listen_sock = self._get_listen_sock(ip, port)
        self.reactor = event.EventBase()
        self.online_users = {}
        self.rooms = {}
        next_21game_time = self._get_next_21game_time()

        listen_event = event.IOEvent(self.listen_sock.fileno(),
                                     event.IO_READ, call_back, arg) # TODO
        game_event = event.TimeEvent(call_back, arg, next_21game_time)

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

>>>>>>> bc0779974670b5c0617e97669a9f93a3a2fb64c5
