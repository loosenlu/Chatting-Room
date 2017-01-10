

import socket
import struct
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




# client class
class Client():

    def __init__(self, ip, port):

        self._get_connect_sock(ip, port)

    def _get_connect_sock(self, ip, port):

        self.connection_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.connection_sock.connect((ip, port))

    def _display(self, display_list):

        for promte in display_list:
            print promte


    def _pack_len(self, length):

        return struct.pack('h', length)

    def _build_packet(self, msg):

        packet_elements = []
        packet_elements.append(PACKET_HEADER)
        packet_elements.append(self._pack_len(len(msg)))
        packet_elements.append(msg)
        return ''.join(packet_elements)

    def _resolve_packet(self, packet):

        return packet[4:]

    def _login(self):

        user_name = raw_input("Username: ").strip()
        password = raw_input("Password: ").strip()
        msg = MSG_TYPE_LOGIN + SEPARATOR.join([user_name, password])
        packet = self._build_packet(msg)
        self.connection_sock.sendall(packet)
        recv_packet = self.connection_sock.recv(4096)
        msg = self._resolve_packet(recv_packet)
        return True if msg == 'Success' else False

    def _register(self):

        user_name = raw_input("Username: ").strip()
        password = raw_input("Password: ").strip()
        msg = MSG_TYPE_REG + SEPARATOR.join([user_name, password])
        packet = self._build_packet(msg)
        self.connection_sock.sendall(packet)
        recv_packet = self.connection_sock.recv(4096)
        msg = self._resolve_packet(recv_packet)
        return True if msg == 'Success' else False

    def _get_room_list(self):

        msg = MSG_TYPE_GET_ROOMS
        packet = self._build_packet(msg)
        self.connection_sock.sendall(packet)
        recv_packet = self.connection_sock.recv(4096)
        msg = self._resolve_packet(recv_packet)
        room_list = msg.split(SEPARATOR)
        self._display(room_list)

    def _get_user_list(self):

        msg = MSG_TYPE_GET_USER
        packet = self._build_packet(msg)
        self.connection_sock.sendall(packet)
        recv_packet = self.connection_sock.recv(4096)
        msg = self._resolve_packet(recv_packet)
        user_list = msg.split(SEPARATOR)
        self._display(user_list)

    def _unitcast(self, user_name, data):

        msg = SEPARATOR.join([MSG_TYPE_UNITCAST, user_name, data])
        packet = self._build_packet(msg)
        self.connection_sock.sendall(packet)

    def _broadcast(self, data):

        msg = SEPARATOR.join([MSG_TYPE_UNITCAST, data])
        packet = self._build_packet(msg)
        self.connection_sock.sendall(packet)

    def _crt_room(self, new_room):

        msg = SEPARATOR.join([MSG_TYPE_CRT_ROOM, new_room])
        packet = self._build_packet(msg)
        self.connection_sock.sendall(packet)

    def _leave_room(self):

        msg = MSG_TYPE_LEAVE_ROOM
        packet = self._build_packet(msg)
        self.connection_sock.sendall(packet)

    def _enter_room(self, new_room):

        msg = SEPARATOR.join([MSG_TYPE_JOIN_ROOM, new_room])
        packet = self._build_packet(msg)
        self.connection_sock.sendall(packet)

    def _resolve_cmd(self, cmd):

        cmd_list = cmd.split()
        if cmd_list[0] == "chat":
            if len(cmd_list) == 3:
                self._unitcast(cmd_list[1], ' '.join(cmd_list[2:]))
            else:
                self._broadcast(' '.join(cmd_list[1:]))
        elif cmd_list[0] == "list":
            if cmd_list[1] == "room":
                self._get_room_list()
            elif cmd_list[1] == "user":
                self._get_user_list()
        elif cmd_list[0] == "leave":
            self._leave_room()
        elif cmd_list[0] == "enter":
            room_name = ' '.join(cmd_list[1:])
            self._enter_room(room_name)
        elif cmd_list[0] == "create":
            room_name = ' '.join(cmd_list[1:])
            self._crt_room(room_name)

    def start(self):

        while True:
            #self._display(["login", "register"])
            cmd = raw_input("You wants: ").strip()
            if cmd == "register":
                if self._register():
                    print "register success!"
                    break
                else:
                    print "register failure, please try again!"
            elif cmd == "login":
                if self._login():
                    print "login success!"
                    break
                else:
                    print "login failure, please try again!"
            else:
                print 'cmd is wrong, please input "register" or "login".'

        while True:
            cmd = raw_input(">> ").strip()
            self._resolve_cmd(cmd)


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
