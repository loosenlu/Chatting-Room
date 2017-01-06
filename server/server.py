
import socket
import time
import event



class Server(object):

    def __init__(self, ip, port):

        self.listen_sock = self._get_listen_sock(ip, port)
        self.reactor = event.EventBase()
        self.online_users = {}
        self.rooms = {}
        # the lobby's ID is 0
        self.room_index = 1
        game_lobby = RoomInfo(0)
        self.rooms[0] = game_lobby

    def _get_listen_sock(self, ip, port):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((ip, port))
        sock.listen(10)

    # def _get_next_21game_time(self):

    #     half_time = 30 * 60
    #     now = time.time()
    #     next_21game_time = (int(now) / half_time + 1) * half_time
    #     return next_21game_time

    def create_room(self):

        new_room = RoomInfo(self.room_index)
        self.rooms[self.room_index] = new_room
        self.room_index += 1

    def del_room(self, room_id):

        del self.rooms[room_id]


    def start(self):
        pass


class RoomInfo(object):
    
    def __init__(self, room_id):

        self.room_id = room_id
        self.members = {}

    def broadcast(self):

        pass

    def add_user(self, user):

        self.members[user.user_id] = user

    def del_user(self, user):

        del self.members[user.user_id]


class UserInfo(object):
    
    def __init__(self, user_id, user_name, connect_sock):

        self.user_id = user_id
        self.user_name = user_name
        self.cur_room = 0
        self.send_buf = SendBuf(connect_sock)
        self.recv_buf = RecvBuf(connect_sock)


class Buffer(object):

    def __init__(self, sock):

        self.sock = sock
        self.buffer = []

    def add(self, msg):

        self.buffer.append(msg)

    
class SendBuf(Buffer):

    def __init__(self, sock):

        Buffer.__init__(sock)
    
    def send(self):
        pass


class RecvBuf(Buffer):

    def __init__(self, sock):

        Buffer.__init__(sock)

    def recv(self):
        pass