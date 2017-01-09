

import socket
import struct


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

    def _display(self):
        pass

    def _pack_len(self, length):

        return struct.pack('h', length)

    def _build_packet(self, msg):

        packet_elements = []
        packet_elements.append(PACKET_HEADER)
        packet_elements.append(self._pack_len(len(msg)))
        return ''.join(packet_elements)

    def _login(self):

        while True:

            user_name = raw_input("Username: ").strip()
            password = raw_input("Password: ").strip()
            msg = SEPARATOR.join([MSG_TYPE_LOGIN, user_name, password])
            packet = self._build_packet(msg)

            self.connection_sock.sendall(packet)
            


    def start(self):

        pass

#   # prompt the user to login
#   def login(self):
#     while True:
#       # enter the username and password
#       username = raw_input('Username: ').strip()
#       password = raw_input('Password: ').strip()

#       # send a login command to the server: "login|username|password"
#       self.connection.send('|'.join([Constants.MSG_LOGIN, username, password]))
#       resp = self.connection.recv(Constants.MAX_MSG_LENGTH)

#       if resp == Constants.MSG_EXIT:
#         # if server exits, close the connection
#         self.connection.close()
#         return False
#       if resp == Constants.MSG_SUCCESS:
#         # login successfully
#         return True
#       elif resp == Constants.MSG_LOGIN_EXCEED_MAX_TIMES:
#         # blocked for 3 consecutive failures
#         print '[Error] 3 consecutive failures, retry after', \
#           Constants.BLOCK_TIME, ' seconds.\n'
#         return False
#       elif resp == Constants.MSG_USER_ALREADY_LOGINED:
#         # already logined in
#         print '[Error] The user', username, 'is online.\n'
#       else:
#         # incorrect combination of username and password.
#         print '[Error] Incorrect username or password.\n'

#   # start the client
#   def start(self):

#       elif self.login():
#         # if login success, start a client thread
#         t = ClientThread(self.address, self.connection)
#         t.start()

#         # print an welcome message
#         print '\nWelcome to simple chat server!\n'
#         while True:
#           # prompt the user to enter a command
#           cmd = raw_input('Command: ')
#           cmd, arg = (cmd + ' ').split(' ', 1)
#           completed_cmd = self.complete_command(cmd)
#           arg = arg.strip()
#           if len(completed_cmd) == 0:
#             # if invalid command entered, display the commands list
#             if cmd != "":
#               print '[Error] Invalid command:', cmd, '\n'
#               self.list_commands()
#           elif len(completed_cmd) > 1:
#             print '[Error] which command?', completed_cmd, '\n'
#           else:
#             cmd = completed_cmd[0]
#             if self.process_command(cmd, arg):
#               break

#       # try to logout quietly
#       self.try_logout()
#     except KeyboardInterrupt:
#       # try to logout quietly
#       self.try_logout()
#     except socket.error as e:
#       print e
#     except:
#       self.try_logout()

#   def process_command(self, cmd, arg):
#     if cmd in [Constants.MSG_WHO_ELSE, Constants.MSG_WHO_LAST_HOUR]:
#       # send whoelse and wholasthr to the server
#       self.connection.send(cmd)
#     elif cmd == Constants.MSG_LOGOUT:
#       # send a logout command, and break the input loop.
#       self.connection.send(cmd)
#       return True
#     elif cmd.startswith(Constants.MSG_BROADCAST):
#       # broadcast command
#       if len(arg) > 0:
#         # send 'broadcast|message' to the server
#         msg = arg
#         self.connection.send('|'.join([Constants.MSG_BROADCAST, msg]))
#       else:
#         # invalid broadcast arguments
#         print '[Error] Usage: broadcast [message]\n'
#     elif cmd.startswith(Constants.MSG_MESSAGE):
#       # message command
#       if arg.count(' ') >= 1:
#         # send 'message|username|message' to the server
#         user, msg = arg.split(' ', 1)
#         self.connection.send('|'.join([Constants.MSG_MESSAGE, user, msg]))
#       else:
#         # invalid message arguments
#         print '[Error] Usage: message [user] [message]\n'
#     return False

#   # try to logout quietly
#   def try_logout(self):
#     try:
#       # send a logout message to server
#       self.connection.send(Constants.MSG_LOGOUT)
#       # close the connection
#       self.connection.close()
#     except socket.error:
#       pass

#   # displays the commands
#   def list_commands(self):
#     print ''
#     print '[command list]'
#     print '  whoelse                 : Displays name of other connected users.'
#     print '  wholasthr               : Displays name of only those users that connected within the last hour.'
#     print '  broadcast <message>     : Broadcasts <message> to all connected users.'
#     print '  message <user> <message>: Private <message> to a <user>.'
#     print '  logout                  : Log out this user.'
#     print ''

#   # return all the commands matches the prefix.
#   def complete_command(self, cmd_prefix):
#     if cmd_prefix == '':
#       return []
#     else:
#       return [command for command in Constants.COMMANDS if command.startswith(cmd_prefix)]


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print "[Error] Usage: python Client.py <server ip> <server port>"
    else:
        try:
            c = Client(sys.argv[1], int(sys.argv[2]))
            c.start()
        except ValueError:
            print '[Error] invalid port'
