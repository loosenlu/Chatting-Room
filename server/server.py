
import socket
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