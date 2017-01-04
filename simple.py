
import event

g_select_timeout = 10

class Server(object):

    def __init__(self, host='127.0.0.1', port=6666, client_nums=10):
        self.__host = host
        self.__port = port
        self.__client_nums = client_nums
        self.__buffer_size = 1024

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(False)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1) #keepalive
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #端口复用

        server_host = (self.__host, self.__port)
        try:
            self.server.bind(server_host)
            self.server.listen(self.__client_nums)
        except:
            raise

        self.inputs = [self.server] #select 接收文件描述符列表  
        self.outputs = [] #输出文件描述符列表
        self.message_queues = {}#消息队列
        self.client_info = {}


if __name__ == "__main__":
