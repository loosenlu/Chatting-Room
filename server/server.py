
import struct
import socket
import time
import event
import os
import platform


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
        # self.no_authorization = {}
        # self.online_users = {}
        self.rooms = {}
        self.rooms["Game Hall"] = Room("Game Hall")
        self.database = self._crt_database()
        self.event_base.add_event(self)

    def _crt_database(self):

        path = os.getcwd()
        if platform.system() == 'Windows':
            database_name = ''.join([path, r'\\', "server_data"])
        else:
            database_name = ''.join([path, '/', "server_data"])
        database_fd = open(database_name, 'w+')
        return database_fd

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
        self.event_base.add_event(new_session)


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
        self.data_container = []
        self.need_to_read = -1

    def _unpack_len(self, len_filed):

        msg_len = struct.unpack('h', len_filed)
        return msg_len[0]

    def _get_packet_info(self, data):

        data = ''.join(self.data_container) + data

        if len(data) < 4:
            self.data_container.append(data)
        else:
            packet_header = data[0:4]
            packet_data = data[4:]
            if packet_header[0:2] != PACKET_HEADER:
                # illegal packet
                self.data_container = []
                self.need_to_read = -1
                self.ready = False
                return
            msg_len = self._unpack_len(packet_header[2:])
            self.data_container.append(packet_data)
            self.need_to_read = msg_len - len(packet_data)

    def _get_packet(self):

        if self.need_to_read == -1:
            # There has two situation:
            # 1. A new packet is comming;
            # 2. Doesn't get the whole packet header.
            try:
                data = self.sock.recv(4096)
                if data == '':
                    # means the peer point has closed the socket
                    self.ready = True
                    return
                self._get_packet_info(data)
            except socket.error:
                # client closed abnormal
                print "Abnormal closed"
        else:
            data = self.sock.recv(self.need_to_read)
            self.data_container.append(data)
            self.need_to_read -= len(data)
        self.ready = (True if self.need_to_read == 0 else False)

    def read(self):

        self._get_packet()
        if not self.ready:
            return None
        else:
            msg = ''.join(self.data_container)
            self.data_container = []
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
        event.IOEvent.__init__(self, self.sock.fileno())
        self.set_io_type(event.EV_IO_READ)

        self.user_name = None
        self.cur_room = None
        self.read_channel = InChannel(self.sock)
        self.write_channel = OutChannel(self.sock)

    def read(self):

        msg = self.read_channel.read()

        if msg == '':
            # peer point has closed the socket
            # need to unregister from the room and the event_base
            self.sock.close()
            old_room = self.cur_room
            self.cur_room.leave(self)
            if old_room.empty():
                self.server.del_room(old_room.room_name)
            self.server.event_base.del_event(self)
        elif msg is not None:
            self._resolve_msg(msg)

    def write(self):

        self.write_channel.write()
        # no msg to send
        if self.write_channel.empty():
            self.server.event_base.mod_event(self.ev_fd, event.EV_IO_READ)

    def add_packet_to_outchannel(self, packet):

        self.write_channel.add_packet(packet)
        old_io_type = self.get_io_type()
        self.server.event_base.mod_event(self.ev_fd,
                                         old_io_type | event.EV_IO_WRITE)

    def _resolve_msg(self, msg):

        msg_type = msg[0:2]
        msg_data = msg[2:]
        if msg_type == MSG_TYPE_REG:
            self._register(msg_data)
        elif msg_type == MSG_TYPE_LOGIN:
            self._login(msg_data)
        elif msg_type == MSG_TYPE_GET_ROOMS:
            self._get_room_list()
        elif msg_type == MSG_TYPE_GET_USER:
            self._get_user_list()
        elif msg_type == MSG_TYPE_CRT_ROOM:
            self._login(msg_data)
        elif msg_type == MSG_TYPE_JOIN_ROOM:
            self._join_room(msg_data)
        elif msg_type == MSG_TYPE_LEAVE_ROOM:
            self._leave_room()
        elif msg_type == MSG_TYPE_UNITCAST:
            self._unitcast(msg_data)
        elif msg_type == MSG_TYPE_BROADCAST:
            self._broadcast(msg)
        elif msg_type == MSG_TYPE_GAME:
            self._game_anwser(msg)
        else:
            pass

    def _check(self, user_name, user_passwd):

        self.server.database.seek(0, os.SEEK_SET)
        for user_info in self.server.database:
            name, passwd, online_time_str = user_info.split(SEPARATOR)
            if name == user_name and passwd == user_passwd:
                return True
        return False

    def _new_user(self, user_name, user_passwd):

        self.server.database.seek(0, os.SEEK_END)
        user_info = SEPARATOR.join([user_name, user_passwd, str(0)])
        self.server.database.write(user_info)

    def _register(self, msg):

        user_name, user_passwd = msg.split(SEPARATOR)
        self._new_user(user_name, user_passwd)
        self.user_name = user_name
        # When user register or login, he/she
        # locate at room "Game Hall"
        self.cur_room = self.server.rooms["Game Hall"]
        self.cur_room.enter(self)
        packet = self._build_packet(MSG_TYPE_REG + "Success")
        self.add_packet_to_outchannel(packet)

    def _login(self, msg):

        user_name, user_passwd = msg.split(SEPARATOR)
        if self._check(user_name, user_passwd):
            self.user_name = user_name
            # When user register or login, he/she
            # locate at room "Game Hall"
            self.cur_room = self.server.rooms["Game Hall"]
            self.cur_room.enter(self)
            packet = self._build_packet(MSG_TYPE_LOGIN + "Success")
        else:
            packet = self._build_packet(MSG_TYPE_LOGIN + "Failure")
        self.add_packet_to_outchannel(packet)

    def _crt_room(self, new_room_name):

        new_room = self.server.crt_room(new_room_name)
        old_room = self.cur_room
        old_room.leave(self)
        new_room.enter(self)
        self.cur_room = new_room
        if old_room.empty():
            self.server.del_room(old_room.room_name)
        new_packet = \
            self._build_packet(MSG_TYPE_CRT_ROOM +
                               "Create room named %s success, now you are at room[%s]"
                               % (new_room_name, new_room_name))
        self.add_packet_to_outchannel(new_packet)

    def _join_room(self, join_room_name):

        try:
            join_room = self.server.rooms[join_room_name]
        except KeyError:
            # Don't has this room
            packet = \
                self._build_packet(MSG_TYPE_JOIN_ROOM +
                                   "Don't have room named %s" % join_room_name)
            self.add_packet_to_outchannel(packet)
        old_room = self.cur_room
        old_room.leave(self)
        join_room.enter(self)
        self.cur_room = join_room
        if old_room.empty():
            self.server.del_room(old_room.room_name)
        packet = \
            self._build_packet(MSG_TYPE_JOIN_ROOM +
                               "Now, you are at room[%s]" % self.cur_room.room_name)
        self.add_packet_to_outchannel(packet)

    def _leave_room(self):

        old_room = self.cur_room
        game_hall = self.server.rooms["Game Hall"]
        old_room.leave(self)
        game_hall.enter(self)
        self.cur_room = game_hall
        if old_room.empty():
            self.server.del_rooms(old_room.room_name)
        packet = \
            self._build_packet(MSG_TYPE_LEAVE_ROOM + "Now, you are at Game Hall!")
        self.add_packet_to_outchannel(packet)

    def _unitcast(self, packet):

        recv_user_name, msg = packet.split(SEPARATOR)
        new_packet = \
            self._build_packet(MSG_TYPE_UNITCAST + SEPARATOR.join([self.user_name, msg]))
        # the unitcast only happen on the same room.
        try:
            recv_user_session = self.cur_room.sessions[recv_user_name]
        except KeyError:
            # Don't have this user
            new_packet = \
                self._build_packet(MSG_TYPE_UNITCAST + "Don't have user named %s" %recv_user_name)
        # Add the packet on the user's Session
        recv_user_session.add_packet_to_outchannel(new_packet)

    def _broadcast(self, packet):

        msg = packet
        new_packet = \
            self._build_packet(MSG_TYPE_BROADCAST + SEPARATOR.join([self.user_name, msg]))
        # For users in the current room
        for _, recv_user_session in self.cur_room.sessions.iteritems():
            recv_user_session.add_packet_to_outchannel(new_packet)

    def _get_room_list(self):

        rooms_list = []
        for room_name in self.server.rooms.keys():
            rooms_list.append(room_name)

        msg = SEPARATOR.join(rooms_list)
        new_packet = self._build_packet(MSG_TYPE_GET_ROOMS + msg)
        self.add_packet_to_outchannel(new_packet)

    def _get_user_list(self):

        users_list = []
        for user_name in self.cur_room.sessions.keys():
            users_list.append(user_name)

        msg = SEPARATOR.join(users_list)
        new_packet = self._build_packet(MSG_TYPE_GET_USER + msg)
        self.add_packet_to_outchannel(new_packet)

    def _game_anwser(self, packet):

        pass

    def _pack_len(self, length):

        return struct.pack('h', length)

    def _build_packet(self, msg):
        """Build packet send to user

        """
        data = []
        msg_len = len(msg)
        data.append(PACKET_HEADER)
        data.append(self._pack_len(msg_len))
        data.append(msg)
        return ''.join(data)



if __name__ == "__main__":

    server_ip = ""
    server_port = 63333

    ev_base = event.EventBase()
    Server(server_ip, server_port, ev_base)

    ev_base.event_loop()