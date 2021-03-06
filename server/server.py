

import struct
import socket
import time
import event
import os
import platform
import random
import sys


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

    def __init__(self, ip, port, base, database_path):

        self.event_base = base
        self._get_listen_sock(ip, port)
        event.IOEvent.__init__(self, self.listen_sock.fileno())
        self.set_io_type(event.EV_IO_READ)
        self.rooms = {}
        self.rooms["Game Hall"] = Room("Game Hall")
        self.event_base.add_event(self)
        self.registered_users = {}
        self.database_path = database_path
        self._get_registered_user()

        game_start_time = self.get_next_21game_time()
        game_timer = GameStartTimer(self, game_start_time)
        self.event_base.add_event(game_timer)

    def read(self):
        """Accept the new client

        """
        conn, _ = self.listen_sock.accept()
        conn.setblocking(0)
        new_session = Session(conn, self, event.EV_IO_READ)
        self.event_base.add_event(new_session)

    def crt_room(self, room_name):
        """Crette a new room

        """
        new_room = Room(room_name)
        self.rooms[room_name] = new_room
        return new_room

    def del_room(self, room_name):
        """Delete room named room_name

        """
        if room_name == "Game Hall":
            return
        del self.rooms[room_name]

    def update_database(self):
        """Store the users infomation

        """
        with open(self.database_path, 'w') as database:

            for user_name, user_info in self.registered_users.iteritems():
                info_container = []
                info_container.append(user_name)
                info_container.append(user_info[0])
                info_container.append(str(user_info[1]))
                database.write(' '.join(info_container) + '\n')

    def get_next_21game_time(self):
        """Calculate the 21game start time

        """
        # For debug, 5 minutes for 21 games
        half_time = 5 * 60
        now = time.time()
        next_21game_time = (int(now) / half_time + 1) * half_time
        return next_21game_time

    def _get_listen_sock(self, ip_address, port):

        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_sock.bind((ip_address, port))
        self.listen_sock.listen(10)

    def _get_registered_user(self):

        if not os.path.exists(self.database_path):
            fd = open(self.database_path, 'w')
            fd.close()
        else:
            with open(self.database_path, 'r') as database:

                for user_info in database:
                    user_name, user_passwd, level = user_info.split()
                    self.registered_users[user_name] = [user_passwd, int(level)]


class Session(event.IOEvent):

    def __init__(self, sock, server, io_type):

        self.sock = sock
        self.server = server
        event.IOEvent.__init__(self, self.sock.fileno())
        self.set_io_type(event.EV_IO_READ)

        self.user_name = None
        self.user_level = None
        self.login_time = None

        self.cur_room = None
        self.read_channel = InChannel(self.sock)
        self.write_channel = OutChannel(self.sock)

    def read(self):
        """Recv the data from connected sock

        """
        self.server.event_base.time_ev_minheap.top()
        try:
            msg = self.read_channel.read()
        except socket.error:
            # abnormal closed
            self._login_out()
            return

        if msg == '':
            # peer point has closed the socket
            # need to unregister from the room and the event_base
            self._login_out()
        elif msg is not None:
            self._resolve_msg(msg)

    def write(self):
        """Send data to peer sock

        """
        self.write_channel.write()
        # no msg to send
        if self.write_channel.empty():
            self.server.event_base.mod_event(self.ev_fd, event.EV_IO_READ)

    def add_packet_to_outchannel(self, packet):
        """Add packet to out channel

        """
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
            self._crt_room(msg_data)
        elif msg_type == MSG_TYPE_JOIN_ROOM:
            self._join_room(msg_data)
        elif msg_type == MSG_TYPE_LEAVE_ROOM:
            self._leave_room()
        elif msg_type == MSG_TYPE_UNITCAST:
            self._unitcast(msg_data)
        elif msg_type == MSG_TYPE_BROADCAST:
            self._broadcast(msg_data)
        elif msg_type == MSG_TYPE_GAME:
            self._game_anwser(msg_data)
        else:
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

    def _check_register(self, user_name):

        if user_name in self.server.registered_users:
            return False
        return True

    def _check_login(self, user_name, user_passwd, ):

        if (user_name in self.server.registered_users and
                user_passwd == self.server.registered_users[user_name][0]):
            return True
        return False

    def _register(self, msg):

        user_name, user_passwd = msg.split(SEPARATOR)
        if not self._check_register(user_name):
            # check whther has the same name
            packet = \
                self._build_packet(MSG_TYPE_REG + "%s has registered." % user_name)
        else:
            # When user register or login, he/she
            # locate at room "Game Hall"
            self.server.registered_users[user_name] = [user_passwd, 0]
            self.user_name = user_name
            self.user_level = 0
            self.login_time = time.time()
            self.cur_room = self.server.rooms["Game Hall"]
            self.cur_room.enter(self)
            packet = self._build_packet(MSG_TYPE_REG + "Success")
            # update the database
            self.server.update_database()
        self.add_packet_to_outchannel(packet)

    def _login(self, msg):

        user_name, user_passwd = msg.split(SEPARATOR)
        if self._check_login(user_name, user_passwd):
            # When user register or login, he/she
            # locate at room "Game Hall"
            self.user_name = user_name
            self.user_level = self.server.registered_users[user_name][1]
            self.login_time = time.time()
            self.cur_room = self.server.rooms["Game Hall"]
            self.cur_room.enter(self)
            packet = self._build_packet(MSG_TYPE_LOGIN + "Success")
        else:
            packet = self._build_packet(MSG_TYPE_LOGIN + "Name/Passwd Wrong!")
        self.add_packet_to_outchannel(packet)

    def _login_out(self):

        up_level = int((time.time() - self.login_time) / 600)
        self.server.registered_users[self.user_name][1] += up_level
        old_room = self.cur_room
        self.cur_room.leave(self)
        if old_room.empty():
            self.server.del_room(old_room.room_name)
        self.server.event_base.del_event(self)
        self.sock.close()
        self.server.update_database()

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
            self.server.del_room(old_room.room_name)
        packet = \
            self._build_packet(MSG_TYPE_LEAVE_ROOM + "Now, you are at Game Hall!")
        self.add_packet_to_outchannel(packet)

    def _unitcast(self, packet):

        recv_user_name, msg = packet.split(SEPARATOR)
        new_packet = \
            self._build_packet(MSG_TYPE_UNITCAST +
                               SEPARATOR.join([self.user_name, str(self.user_level), msg]))
        # the unitcast only happen on the same room.
        try:
            recv_user_session = self.cur_room.sessions[recv_user_name]
        except KeyError:
            # Don't have this user
            new_packet = \
                self._build_packet(MSG_TYPE_UNITCAST +
                                   "Room[%s] don't have user named %s"
                                   %(self.cur_room.room_name, recv_user_name))
            return
        # Add the packet on the user's Session
        recv_user_session.add_packet_to_outchannel(new_packet)

    def _broadcast(self, packet):

        msg = packet
        new_packet = \
            self._build_packet(MSG_TYPE_BROADCAST +
                               SEPARATOR.join([self.user_name, str(self.user_level), msg]))
        # For users in the current room
        for _, recv_user_session in self.cur_room.sessions.iteritems():
            if self.user_name == recv_user_session.user_name:
                continue
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

        msg = packet
        if self.cur_room.game_on_flag:
            self.cur_room.get_answer(self, msg)
        else:
            new_packet = self._build_packet(MSG_TYPE_GAME + "Game off now!")
            self.add_packet_to_outchannel(new_packet)


class Room(object):

    def __init__(self, room_name):

        self.room_name = room_name
        self.sessions = {}
        self.best_answer = None
        self.game_on_flag = False

    def game_start(self):
        """Start the 21 game.

        """
        self.game_on_flag = True
        number_list = [str(random.randint(1, 10)) for i in xrange(4)]
        number_sequence = ' '.join(number_list)
        msg = SEPARATOR.join(["start", number_sequence])
        self._broadcast(msg)

    def get_answer(self, user, msg):
        """Get the answer from user.

        """
        try:
            answer = eval(msg)
        except:
            packet = \
                self._build_packet(MSG_TYPE_GAME + "Input expression is not illegal!")
            user.add_packet_to_outchannel(packet)
            return

        if answer <= 0 or answer > 21:
            packet = \
                self._build_packet(MSG_TYPE_GAME + "Out of the range[1-21]!")
            user.add_packet_to_outchannel(packet)
            return

        if self.best_answer is None:
            self.best_answer = (answer, user.user_name)
        elif self.best_answer[0] < answer:
            self.best_answer = (answer, user.user_name)

    def game_end(self):
        """End the 21 game.

        """
        self.game_on_flag = False
        if self.best_answer is None:
            result = "No winner"
        else:
            user_name = self.best_answer[1]
            result = "The winner is %s" % user_name
        msg = SEPARATOR.join(["end", result])
        self._broadcast(msg)

    def leave(self, session):
        """Leave this room.

        """
        del self.sessions[session.user_name]

    def enter(self, session):
        """Enter this room.

        """
        self.sessions[session.user_name] = session

    def empty(self):

        return len(self.sessions) == 0

    def _broadcast(self, msg):

        packet = self._build_packet(MSG_TYPE_GAME + msg)
        for user in self.sessions.itervalues():
            user.add_packet_to_outchannel(packet)

    def _build_packet(self, msg):

        data = []
        msg_len = len(msg)
        data.append(PACKET_HEADER)
        data.append(self._pack_len(msg_len))
        data.append(msg)
        return ''.join(data)

    def _pack_len(self, length):

        return struct.pack('h', length)


class GameStartTimer(event.TimeEvent):

    def __init__(self, server, timeval):

        event.TimeEvent.__init__(self, timeval)
        self.server = server

    def call_back(self):

        for each_room in self.server.rooms.itervalues():
            each_room.game_start()

        # Game duration is 15 second
        game_end_time = time.time() + 15
        end_timer = GameEndTimer(self.server, game_end_time)
        self.server.event_base.add_event(end_timer)


class GameEndTimer(event.TimeEvent):

    def __init__(self, server, timeval):

        event.TimeEvent.__init__(self, timeval)
        self.server = server

    def call_back(self):

        for each_room in self.server.rooms.itervalues():
            each_room.game_end()

        next_time = self.server.get_next_21game_time()
        start_time = GameStartTimer(self.server, next_time)
        self.server.event_base.add_event(start_time)


class InChannel(object):

    def __init__(self, sock):

        self.sock = sock
        self.ready = False
        self.data_container = []
        self.need_to_read = -1

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

    def _get_packet(self):

        if self.need_to_read == -1:
            # There has two situation:
            # 1. A new packet is comming;
            # 2. Doesn't get the whole packet header.
            data = self.sock.recv(4096)
            if data == '':
                    # means the peer point has closed the socket
                self.ready = True
                return
            self._get_packet_info(data)
        else:
            data = self.sock.recv(self.need_to_read)
            self.data_container.append(data)
            self.need_to_read -= len(data)
        self.ready = (True if self.need_to_read == 0 else False)

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

    def _unpack_len(self, len_filed):

        msg_len = struct.unpack('h', len_filed)
        return msg_len[0]


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



if __name__ == "__main__":


    if len(sys.argv) != 3:
        print "[Error] Usage: python server.py <server ip> <server port>"

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    if platform.system() == "Windows":
        database_path = ''.join([os.getcwd(), r"\\", "database"])
    else:
        database_path = ''.join([os.getcwd(), '/', "database"])

    ev_base = event.EventBase()

    Server(server_ip, server_port, ev_base, database_path)
    ev_base.event_loop()
