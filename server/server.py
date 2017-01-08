import socket
import time
import event


PACKET_HEADER = 'NE'

MSG_TYPE_REG = 'RE'
MSG_TYPE_LOGIN = 'LO'

MSG_TYPE_CRT_ROOM = 'CR'
MSG_TYPE_JOIN_ROOM = 'JO'
MSG_TYPE_LEAVE_ROOM = 'LR'

MSG_TYPE_GET_ROOMS = 'GR'
MSG_TYPE_GET_USER = 'GU'

MSG_TYPE_UNITCAST = 'UN'
MSG_TYPE_BROADCAST = 'BR'

MSG_TYPE_GAME = 'GA'

SEPARATOR = chr(0)


class Server(event.IOEvent):

    def __init__(self, ip, port, base):

        self.event_base = base
        self._get_listen_sock(ip, port)
        event.IOEvent.__init__(self, self.listen_sock.fileno())
        self.set_io_type(event.EV_IO_READ)
        self.no_authorization = {}
        self.online_users = {}

        self.rooms = {}
        self.rooms[0] = Room("Game Hall")

        self.event_base.add_event(self)

    def _get_listen_sock(self, ip_address, port):

        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_sock.bind((ip_address, port))
        self.listen_sock.listen(10)

    def crt_room(self, room_name):

        new_room = Room(room_name)
        self.rooms[room_name] = new_room
        return new_room

    def del_room(self, room_name):

        del self.rooms[room_name]

    def _get_next_21game_time(self):

        half_time = 30 * 60
        now = time.time()
        next_21game_time = (int(now) / half_time + 1) * half_time
        return next_21game_time

    def read(self):

        conn, _ = self.listen_sock.accept()
        conn.setblocking(0)
        new_session = Session(conn, self, event.EV_IO_READ)
        self.no_authorization[conn.fileno()] = new_session
        self.event_base.event_add(new_session)


class Room(object):

    def __init__(self, room_name):

        self.room_name = room_name
        self.sessions = {}

    def leave(self, session):

        del self.sessions[session.user_name]

    def enter(self, session):

        self.sessions[session.user_name] = session

    def empty(self):

        return len(self.sessions) == 0


class InChannel(object):

    def __init__(self, sock):

        self.sock = sock
        self.ready = False
        self.msg_container = []
        self.need_to_read = -1

    def _parse_length(self, len):

        pass

    def _resolve_header(self, packet):

        #  0           2           4           6           8           N
        #  +-----+-----+-----+-----+-----+-----+-----+-----+-----------+
        #  |           |           |           |                       |
        #  |    'NE'   |   LENGTH  |    TYPE   |        MSSAGE         |
        #  |           |           |           |                       |
        #  +-----+-----+-----+-----+-----+-----+-----+-----+-----------+

        # 'NE' is the identifier of MSG

        if len(packet) < 4:
            self.msg_container.append(packet)
            return

        if len(self.msg_container) != 0:
            self.msg_container.append(packet)
            packet = ''.join(self.msg_container)
            if len(packet) < 4:
                self.msg_container.append(packet)
                return
            self.msg_container = []

        packet_len = len(packet)
        if packet[0:2] != MSG_HEADER:
            # illegal packet
            self.msg_container = []
            self.ready = False
            self.need_to_read = -1
        else:
            msg = packet[4:]
            total_to_read = self._parse_length(packet[2:4])
            self.msg_container.append(msg)
            self.need_to_read = total_to_read - len(msg)
            self.ready = True if self.need_to_read == 0 else False

    def _read(self):

        if self.need_to_read == -1:
            # There are two situation:
            # 1. A new packet is comming;
            # 2. Doesn't get whole info about packet header
            data = self.sock.recv(4096)
            self._resolve_header(data)
        else:
            data = self.sock.recv(self.need_to_read)
            self.msg_container.append(data)
            self.need_to_read -= len(data)
            self.ready = True if self.need_to_read == 0 else False


    def read(self):

        self._read()
        if not self.ready:
            return None
        else:
            msg = ''.join(self.msg_container)
            self.msg_container = []
            self.ready = False
            self.need_to_read = -1
            return msg


class OutChannel(object):

    def __init__(self, sock):

        self.sock = sock
        self.packet_container = []
        self.has_send = 0

    def write(self):

        packet = self.packet_container[0]
        self.has_send += self.sock.send(packet[self.has_send:])
        if self.has_send == len(packet):
            self.has_send = 0
            del self.packet_container[0]

    def empty(self):

        return len(self.packet_container) == 0

    def add_packet(self, packet):

        self.packet_container.append(packet)


class Session(event.IOEvent):

    def __init__(self, sock, server, io_type):

        self.sock = sock
        self.server = server
        self.user_name = None
        self.cur_room = None

        event.IOEvent.__init__(self.sock.fileno(), io_type)
        self.authorization = False
        self.read_channel = InChannel(self.sock)
        self.write_channel = OutChannel(self.sock)

    def read(self):

        msg = self.read_channel.read()
        if msg is not None:
            self._resolve_msg(msg)

    def write(self):

        self.write_channel.write()
        # no msg to send
        if self.write_channel.empty():
            self.set_io_type(event.EV_IO_READ)

    def _resolve_msg(self, msg):

        pass

    def _check(self, user_name, user_passwd):
        pass

    def _new_user(self, user_name, user_passwd):
        pass

    def _register(self, msg):

        user_name, user_passwd = msg.split(SEPARATOR)
        self._new_user(user_name, user_passwd)
        self.user_name = user_name
        self.cur_room = "Game Hall"
        self.server.rooms[self.cur_room].enter(self)
        self.authorization = True
        packet = self._build_packet("Registration Success!")
        self.write_channel.add_packet(packet)

    def _login(self, msg):

        user_name, user_passwd = msg.split(SEPARATOR)
        self._check(user_name, user_passwd)
        self.user_name = user_name
        self.cur_room = "Game Hall"
        self.server.rooms[self.cur_room].enter(self)
        self.authorization = True
        packet = self._build_packet("Login Success!")
        self.write_channel.add_packet(packet)

    def _crt_room(self, new_room_name):

        new_room = self.server.crt_room(new_room_name)
        old_room = self.server.rooms[self.cur_room]
        old_room.leave(self)
        new_room.enter(self)
        self.cur_room = new_room_name
        if old_room.empty():
            self.server.del_room(old_room.room_name)

    def _join_room(self, join_room_name):

        join_room = self.server.rooms[join_room_name]
        old_room = self.server.rooms[self.cur_room]
        old_room.leave(self)
        join_room.enter(self)
        self.cur_room = join_room_name
        if old_room.empty():
            self.server.del_room(old_room.room_name)

    def _unitcast(self, packet):

        user_name, msg = packet.split(SEPARATOR)
        new_packet = self._build_packet(msg)
        current_room = self.server.rooms[self.cur_room]
        user_session = current_room.users[user_name]
        user_session.write_channel.add_packet(new_packet)

    def _broadcast(self, packet):

        msg = packet
        new_packet = self._build_packet(msg)
        current_room = self.server.rooms[self.cur_room]
        for _, user_session in current_room.sessions.iteritems():
            user_session.add_packet(new_packet)

    def _leave_room(self):

        old_room = self.server.rooms[self.cur_room]
        game_hall = self.server.rooms["Game Hall"]
        old_room.leave(self)
        game_hall.enter(self)
        self.cur_room = "Game Hall"
        if old_room.empty():
            self.server.del_rooms(old_room.room_name)

    def _get_room_list(self):

        rooms_list = []
        for room_name in self.server.rooms.keys():
            rooms_list.append(room_name)

        msg = SEPARATOR.join(rooms_list)
        new_packet = self._build_packet(msg)
        self.write_channel.add_packet(new_packet)

    def _get_user_list(self):

        users_list = []
        cur_room = self.server.rooms[self.cur_room]
        for user_name in cur_room.sessions.keys():
            users_list.append(user_name)

        msg = SEPARATOR.join(users_list)
        new_packet = self._build_packet(msg)
        self.write_channel.add_packet(new_packet)

    def _game_anwser(self, packet):

        msg = packet
        pass

    def _pack_number(self, num):
        pass

    def _build_packet(self, msg):
        """Build packet send to user

        """
        data = []
        msg_len = len(msg)
        data.append()
        data.append(self._pack_number(msg_len))
        data.append(msg)
        return ''.join(data)
