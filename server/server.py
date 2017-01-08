import socket
import time
import event


MSG_HEADER = 'NE'

class Server(event.IOEvent):

    def __init__(self, ip, port, base):

        self.event_base = base
        self._get_listen_sock(ip, port)
        event.IOEvent.__init__(self, self.listen_sock.fileno())
        self.set_io_type(event.EV_IO_READ)
        self.no_authorization = {}
        self.online_users = {}
        self.rooms = {}
        self.event_base.add_event(self)

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
        new_session = Session(conn, self, event.EV_IO_READ)
        self.no_authorization[conn.fileno()] = new_session
        self.event_base.event_add(new_session)


class InChannel(object):

    def __init__(self, sock):

        self.sock = sock
        self.ready = False
        self.msg_container = []
        self.need_to_read = -1

    def _parse_length(self, len):

        pass

    def _resolve_header(self, packet):

        #  0           1           2           3           4           N
        #  +-----+-----+-----+-----+-----+-----+-----+-----+-----------+
        #  |           |                       |           |           |
        #  |   HEADER  |         LENGTH        |    TYPE   |    MSG    |
        #  |   (0xFF)  |                       |           |           |
        #  +-----+-----+-----+-----+-----+-----+-----+-----+-----------+

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
        self.msg_container = []
        self.has_send = 0

    def write(self):

        msg = self.msg_container[0]
        self.has_send += self.sock.send(msg[self.has_send:])
        if self.has_send == len(msg):
            self.has_send = 0
            del self.msg_container[0]

    def empty(self):

        return len(self.msg_container) == 0

    def add_msg(self, msg):

        self.msg_container.append(msg)


class Session(event.IOEvent):

    def __init__(self, sock, server, io_type):

        self.sock = sock
        self.server = server
        self.user_id = -1
        event.IOEvent.__init__(self.sock.fileno(), io_type)
        self.authorization = False
        self.read_channel = InChannel(self.sock)
        self.write_channel = OutChannel(self.sock)

    def read(self):

        msg = self.read_channel.read()
        if msg is not None:
            self.process_msg_in(msg)

    def write(self):

        self.write_channel.write()
        # no msg to send
        if self.write_channel.empty():
            self.set_io_type(event.EV_IO_READ)

    def process_msg_in(self, msg):

        pass