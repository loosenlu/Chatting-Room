

import socket
import select


EV_READ = 0
EV_WRITE = 1

class UnknowType(Exception):
    pass



class SelectOp(object):

    def __init__(self):
        self.read_set = []
        self.write_set = []

    def select_add(self, fd, events):

        if events == EV_READ:
            self.read_set.append(fd)
        elif events == EV_WRITE:
            self.write_set.append(fd)
        else:
            raise UnknowType()

    def select_del(self):
        pass

    def select_dispatch(self):
        pass



class Epoll(object):

    def __init__(self):
        pass

    def epoll_add(self):
        pass

    def epoll_del(self):
        pass

    def epoll_dispatch(self):
        pass


class Kqueue(object):

    def __init__(self):
        pass

    def kqueue_add(self):
        pass

    def kqueue_del(self):
        pass

    def kqueue_dispatch(self):
        pass



class EventOp(object):


    def event_add(self, fd, events):
        pass
    
    def event_del(self, fd, events):
        pass

    def dispatch(self, timeval):
        pass


class EventBase(object):

    def __init__(self):
        pass