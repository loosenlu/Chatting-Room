

import socket
import struct
import sys
import threading


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




# client class
# class Client():

#     def __init__(self, ip, port):

#         self._get_connect_sock(ip, port)

#     def _get_connect_sock(self, ip, port):

#         self.connection_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
#         self.connection_sock.connect((ip, port))

#     def _display(self, display_list):

#         for promte in display_list:
#             print promte


#     def _pack_len(self, length):

#         return struct.pack('h', length)

#     def _build_packet(self, msg):

#         packet_elements = []
#         packet_elements.append(PACKET_HEADER)
#         packet_elements.append(self._pack_len(len(msg)))
#         packet_elements.append(msg)
#         return ''.join(packet_elements)

#     def _resolve_packet(self, packet):

#         return packet[4:]

#     def _login(self):

#         user_name = raw_input("Username: ").strip()
#         password = raw_input("Password: ").strip()
#         msg = MSG_TYPE_LOGIN + SEPARATOR.join([user_name, password])
#         packet = self._build_packet(msg)
#         self.connection_sock.sendall(packet)
#         recv_packet = self.connection_sock.recv(4096)
#         msg = self._resolve_packet(recv_packet)
#         return True if msg == 'Success' else False

#     def _register(self):

#         user_name = raw_input("Username: ").strip()
#         password = raw_input("Password: ").strip()
#         msg = MSG_TYPE_REG + SEPARATOR.join([user_name, password])
#         packet = self._build_packet(msg)
#         self.connection_sock.sendall(packet)
#         recv_packet = self.connection_sock.recv(4096)
#         msg = self._resolve_packet(recv_packet)
#         return True if msg == 'Success' else False

#     def _get_room_list(self):

#         msg = MSG_TYPE_GET_ROOMS
#         packet = self._build_packet(msg)
#         self.connection_sock.sendall(packet)
#         recv_packet = self.connection_sock.recv(4096)
#         msg = self._resolve_packet(recv_packet)
#         room_list = msg.split(SEPARATOR)
#         self._display(room_list)

#     def _get_user_list(self):

#         msg = MSG_TYPE_GET_USER
#         packet = self._build_packet(msg)
#         self.connection_sock.sendall(packet)
#         recv_packet = self.connection_sock.recv(4096)
#         msg = self._resolve_packet(recv_packet)
#         user_list = msg.split(SEPARATOR)
#         self._display(user_list)

#     def _unitcast(self, user_name, data):

#         msg = SEPARATOR.join([MSG_TYPE_UNITCAST, user_name, data])
#         packet = self._build_packet(msg)
#         self.connection_sock.sendall(packet)

#     def _broadcast(self, data):

#         msg = SEPARATOR.join([MSG_TYPE_UNITCAST, data])
#         packet = self._build_packet(msg)
#         self.connection_sock.sendall(packet)

#     def _crt_room(self, new_room):

#         msg = SEPARATOR.join([MSG_TYPE_CRT_ROOM, new_room])
#         packet = self._build_packet(msg)
#         self.connection_sock.sendall(packet)

#     def _leave_room(self):

#         msg = MSG_TYPE_LEAVE_ROOM
#         packet = self._build_packet(msg)
#         self.connection_sock.sendall(packet)

#     def _enter_room(self, new_room):

#         msg = SEPARATOR.join([MSG_TYPE_JOIN_ROOM, new_room])
#         packet = self._build_packet(msg)
#         self.connection_sock.sendall(packet)

#     def _resolve_cmd(self, cmd):

#         cmd_list = cmd.split()
#         if cmd_list[0] == "chat":
#             if len(cmd_list) == 3:
#                 self._unitcast(cmd_list[1], ' '.join(cmd_list[2:]))
#             else:
#                 self._broadcast(' '.join(cmd_list[1:]))
#         elif cmd_list[0] == "list":
#             if cmd_list[1] == "room":
#                 self._get_room_list()
#             elif cmd_list[1] == "user":
#                 self._get_user_list()
#         elif cmd_list[0] == "leave":
#             self._leave_room()
#         elif cmd_list[0] == "enter":
#             room_name = ' '.join(cmd_list[1:])
#             self._enter_room(room_name)
#         elif cmd_list[0] == "create":
#             room_name = ' '.join(cmd_list[1:])
#             self._crt_room(room_name)

#     def start(self):

#         while True:
#             #self._display(["login", "register"])
#             cmd = raw_input("You wants: ").strip()
#             if cmd == "register":
#                 if self._register():
#                     print "register success!"
#                     break
#                 else:
#                     print "register failure, please try again!"
#             elif cmd == "login":
#                 if self._login():
#                     print "login success!"
#                     break
#                 else:
#                     print "login failure, please try again!"
#             else:
#                 print 'cmd is wrong, please input "register" or "login".'

#         while True:
#             cmd = raw_input(">> ").strip()
#             self._resolve_cmd(cmd)


class RecvThread(threading.Thread):

    def __init__(self, sock):

        threading.Thread.__init__(self)
        self.recv_sock = sock

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
            display_info = ''.join(["[Private]", user, '(', level, '): ', msg])
            print display_info
        elif msg_type == MSG_TYPE_BROADCAST:
            user, level, msg = data.split(SEPARATOR)
            display_info = ''.join(["[Public]", user, '(', level, '): ', msg])
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

    def _resolve_msg(self, msg):

        msg_type = msg[0:2]
        msg_data = msg[2:0]

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
            self._display_msg(msg, MSG_TYPE_UNITCAST)

        elif msg_type == MSG_TYPE_BROADCAST:
            self._display_msg(msg, MSG_TYPE_BROADCAST)

        elif msg_type == MSG_TYPE_GAME:
            pass
        else:
            raise "unknown msg type!"

    def run(self):

        while True:
            msg = self._recv_packet()
            self._resolve_msg(msg)


class Client(object):

    def __init__(self, server_ip, server_port):

        self._get_connect_sock(server_ip, server_port)

    def _get_connect_sock(self, server_ip, server_port):

        self.connected_sock = \
            socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        try:
            self.connected_sock.connect((server_ip, server_port))
        except socket.error:
            print "Connection has Error!"

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
            if cmd_list[1] == "user":
                self._process_get_user()
            else:
                print "The commond is not correct!"

        elif cmd_list[0] == "chat":
            user_name = cmd_list[1]
            msg_data = ''.join(cmd_list[2:])
            self._process_unicast(SEPARATOR.join([user_name, msg_data]))

        elif cmd_list[0] == MSG_TYPE_BROADCAST:
            user_name = cmd_list[1]
            msg_data = ''.join(cmd_list[2:])
            self._process_broadcast(SEPARATOR.join([user_name, msg_data]))

        elif cmd_list[0] == "game":
            pass

        else:
            raise "unknown msg type!"



if __name__ == '__main__':

    # if len(sys.argv) != 3:
    #     print "[Error] Usage: python Client.py <server ip> <server port>"
    # else:
    #     try:
    #         c = Client(sys.argv[1], int(sys.argv[2]))
    #         c.start()
    #     except ValueError:
    #         print '[Error] invalid port'
    c = Client("localhost", 63333)
    c.start()