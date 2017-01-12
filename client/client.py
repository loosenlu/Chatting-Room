

import socket
import struct
import sys
import threading
import time

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


class RecvThread(threading.Thread):

    def __init__(self, sock):

        threading.Thread.__init__(self)
        self.recv_sock = sock

    def run(self):

        while True:
            msg = self._recv_packet()
            self._resolve_msg(msg)

    def _resolve_msg(self, msg):

        msg_type = msg[0:2]
        msg_data = msg[2:]

        if msg_type == MSG_TYPE_CRT_ROOM:
            self._crt_room_msg(msg_data)

        elif msg_type == MSG_TYPE_JOIN_ROOM:
            self._join_room_msg(msg_data)

        elif msg_type == MSG_TYPE_LEAVE_ROOM:
            self._leave_room_msg(msg_data)

        elif msg_type == MSG_TYPE_GET_ROOMS:
            self._get_room_list(msg_data)

        elif msg_type == MSG_TYPE_GET_USER:
            self._get_user_list(msg_data)

        elif msg_type == MSG_TYPE_UNITCAST:
            self._display_msg(msg_data, MSG_TYPE_UNITCAST)

        elif msg_type == MSG_TYPE_BROADCAST:
            self._display_msg(msg_data, MSG_TYPE_BROADCAST)

        elif msg_type == MSG_TYPE_GAME:
            self._get_game_info(msg_data)
        else:
            raise "unknown msg type!"

    def _unpack(self, length):

        length = struct.unpack('h', length)
        return length[0]

    def _recv_packet(self):

        packet_header = self.recv_sock.recv(4)
        msg_len = self._unpack(packet_header[2:])
        # In the client, the socket is blocked.
        msg = self.recv_sock.recv(msg_len)
        return msg

    def _display_notification(self, title, msg):

        egde_blank_num = 4
        length = egde_blank_num * 2 + max(len(title), len(msg))
        print '=' * length
        print ''.join([' ' * egde_blank_num, title, ' ' * egde_blank_num])
        print '=' * length
        print ''.join([' ' * egde_blank_num, msg, ' ' * egde_blank_num])
        print '-' * length


    def _display_list(self, title, item_list):

        egde_blank_num = 4
        length = egde_blank_num * 2 + len(title)
        print '=' * length
        print ''.join([' ' * egde_blank_num, title, ' ' * egde_blank_num])
        print '=' * length
        for item in item_list:
            print '+ ' + item
        print '-' * length


    def _display_msg(self, data, msg_type):

        if msg_type == MSG_TYPE_UNITCAST:
            user, level, msg = data.split(SEPARATOR)
            display_info = ''.join(["[Private]", user, '(Level-', str(level), '): ', msg])
            print display_info

        elif msg_type == MSG_TYPE_BROADCAST:
            user, level, msg = data.split(SEPARATOR)
            display_info = ''.join(["[Public]", user, '(Level-', str(level), '): ', msg])
            print display_info

        else:
            raise ValueError("Unknown MSG type")

    def _crt_room_msg(self, msg):

        self._display_notification("ROOM MESSAGE", msg)

    def _join_room_msg(self, msg):

        self._display_notification("ROOM MESSAGE", msg)

    def _leave_room_msg(self, msg):

        self._display_notification("ROOM MESSAGE", msg)

    def _get_room_list(self, msg):

        room_list = msg.split(SEPARATOR)
        self._display_list("ROOM LIST", room_list)

    def _get_user_list(self, msg):

        user_list = msg.split(SEPARATOR)
        self._display_list("USER LIST", user_list)

    def _get_game_info(self, msg):

        msg_item = msg.split(SEPARATOR)
        if msg_item[0] == "start":
            msg = "The numbers are: " + msg_item[1]
            self._display_notification("21 game(start)", msg)
        elif msg_item[0] == "end":
            msg = msg_item[1]
            self._display_notification("21 game(end)", msg)
        else:
            self._display_notification("21 game", msg)


class Client(object):

    cmd_type_list = [
        "help -- For help",
        "chat user_name msg -- send msg to user named user_name",
        "all msg -- send msg to everyone that in the room you locate at now",
        "create room_name -- create a new room",
        "enter room_name -- enter room",
        "leave -- leave room and return Game Hall",
        "list room -- get room list",
        "list user -- get user list",
        "quit -- quit program"
    ]

    def __init__(self, server_ip, server_port):

        self._get_connect_sock(server_ip, server_port)
        self.quit = False

    def start(self):

        self._login_register()
        recv_thread = RecvThread(self.connected_sock)
        recv_thread.setDaemon(True)
        recv_thread.start()

        while not self.quit:
            time.sleep(0.1)
            cmd = raw_input(">> ").strip()
            if cmd == '':
                continue
            self._resolve_cmd(cmd)

    def _login_register(self):

        self._display_list("Welcome the Chatting Room!", ["Login", "Register"])

        while True:
            cmd = raw_input("Do you want: ")
            if cmd == "Register":
                user_name = raw_input("Username: ").strip()
                if ' ' in user_name:
                    print "The name can't has blank."
                    continue
                password = raw_input("Password: ").strip()
                msg = MSG_TYPE_REG + SEPARATOR.join([user_name, password])
                packet = self._build_packet(msg)
                self.connected_sock.sendall(packet)
                recv_packet = self.connected_sock.recv(4096)
                # There is for simple, it is not correct anytime.
                msg = recv_packet[6:]
                if msg == "Success":
                    print "Register Successful!"
                    self._display_list("Usage", Client.cmd_type_list)
                    break
                else:
                    print msg
                    continue

            elif cmd == "Login":
                user_name = raw_input("Username: ").strip()
                if ' ' in user_name:
                    print "The name can't has blank."
                    continue
                password = raw_input("Password: ").strip()
                msg = MSG_TYPE_LOGIN + SEPARATOR.join([user_name, password])
                packet = self._build_packet(msg)
                self.connected_sock.sendall(packet)
                recv_packet = self.connected_sock.recv(4096)
                # There is for simple, it is not correct anytime.
                msg = recv_packet[6:]
                if msg == "Success":
                    print "Login Successful!"
                    self._display_list("Usage", Client.cmd_type_list)
                    break
                else:
                    print msg
                    continue

            else:
                print "Command wrong, [Login] or [Register]"

    def _resolve_cmd(self, cmd):

        cmd_list = cmd.split()

        if cmd_list[0] == "create":
            cmd_data = ''.join(cmd_list[1:])
            self._process_crt_room(cmd_data)

        elif cmd_list[0] == "enter":
            cmd_data = ''.join(cmd_list[1:])
            self._process_join_room(cmd_data)

        elif cmd_list[0] == "leave":
            cmd_data = ''.join(cmd_list[1:])
            self._process_leave_room(cmd_data)

        elif cmd_list[0] == "list":
            if cmd_list[1] == "room":
                self._process_get_room()
            elif cmd_list[1] == "user":
                self._process_get_user()
            else:
                print "list commond is not correct!"

        elif cmd_list[0] == "chat":
            user_name = cmd_list[1]
            msg_data = ''.join(cmd_list[2:])
            self._process_unicast(SEPARATOR.join([user_name, msg_data]))

        elif cmd_list[0] == "all":
            msg_data = ''.join(cmd_list[1:])
            self._process_broadcast(msg_data)

        elif cmd_list[0] == "game":
            msg_data = ''.join(cmd_list[1:])
            print msg_data
            self._process_game(msg_data)

        elif cmd_list[0] == "quit":
            self.quit = True
            self.connected_sock.close()

        elif cmd_list[0] == "help":
            self._display_list("Usage", Client.cmd_type_list)

        else:
            raise "unknown msg type!"

    def _get_connect_sock(self, server_ip, server_port):

        self.connected_sock = \
            socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        try:
            self.connected_sock.connect((server_ip, server_port))
        except socket.error:
            print "Connection has Error!"

    def _display_list(self, title, item_list):

        egde_blank_num = 4
        length = egde_blank_num * 2 + len(title)
        print '=' * length
        print ''.join([' ' * egde_blank_num, title, ' ' * egde_blank_num])
        print '=' * length
        for item in item_list:
            print '+ ' + item
        print '-' * length

    def _pack_len(self, length):

        return struct.pack('h', length)

    def _build_packet(self, msg):

        return ''.join([PACKET_HEADER, self._pack_len(len(msg)), msg])

    def _process_crt_room(self, cmd_data):

        msg = MSG_TYPE_CRT_ROOM + cmd_data
        packet = self._build_packet(msg)
        self.connected_sock.sendall(packet)

    def _process_join_room(self, cmd_data):

        msg = MSG_TYPE_JOIN_ROOM + cmd_data
        packet = self._build_packet(msg)
        self.connected_sock.sendall(packet)

    def _process_leave_room(self, cmd_data):

        msg = MSG_TYPE_LEAVE_ROOM + cmd_data
        packet = self._build_packet(msg)
        self.connected_sock.sendall(packet)

    def _process_get_room(self):

        msg = MSG_TYPE_GET_ROOMS
        packet = self._build_packet(msg)
        self.connected_sock.sendall(packet)

    def _process_get_user(self):

        msg = MSG_TYPE_GET_USER
        packet = self._build_packet(msg)
        self.connected_sock.sendall(packet)

    def _process_unicast(self, msg_data):

        msg = MSG_TYPE_UNITCAST + msg_data
        packet = self._build_packet(msg)
        self.connected_sock.sendall(packet)

    def _process_broadcast(self, msg_data):

        msg = MSG_TYPE_BROADCAST + msg_data
        packet = self._build_packet(msg)
        self.connected_sock.sendall(packet)

    def _process_game(self, msg_data):

        msg = MSG_TYPE_GAME + msg_data
        packet = self._build_packet(msg)
        self.connected_sock.sendall(packet)

if __name__ == '__main__':

    # if len(sys.argv) != 3:
    #     print "[Error] Usage: python Client.py <server ip> <server port>"
    # else:
    #     try:
    #         c = Client(sys.argv[1], int(sys.argv[2]))
    #         c.start()
    #     except ValueError:
    #         print '[Error] invalid port'
    c = Client("localhost", 63334)
    c.start()