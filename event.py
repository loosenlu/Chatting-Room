

import socket
import select
import platform


EV_READ = 0x01
EV_WRITE = 0x02
EV_RDWT = 0x03

class UnknowType(Exception):
    pass



class SelectOp(object):

    def __init__(self):

        self.read_set = []
        self.write_set = []


    def select_add(self, fd, event_type):

        if event_type == EV_READ:
            self.read_set.append(fd)
        elif event_type == EV_WRITE:
            self.write_set.append(fd)
        else:
            raise UnknowType()


    def select_del(self, fd, event_type):
        
        if event_type & EV_READ:
            self.write_set.remove(fd)
        elif event_type & EV_WRITE:
            self.write_set.remove(fd)
        else:
            # log
            raise UnknowType()


    def select_dispatch(self, timeout):

        read_events, write_events, exception_events = \
            select.select(self.read_set, self.write_set, [], timeout)

        active_list = []
        for i in read_events:
            active_list.append((i, EV_READ))
        for i in write_events:
            active_list.append((i, EV_WRITE))

        return active_list



class EpollOp(object):

    def __init__(self):

        self.epollfd = select.epoll()


    def epoll_add(self, fd, event_type):

        if event_type & EV_READ:
            self.epollfd.register(fd, select.EPOOLIN)
        elif event_type & EV_WRITE:
            self.epollfd.register(fd, select.EPOOLOUT)
        else:
            #log
            raise UnknowType()


    def epoll_del(self, fd, event_type):

        # TODO
        self.epollfd.unregister(fd)


    def epoll_dispatch(self, timeout):

        events = self.epollfd.epoll(timeout)

        active_list = []
        for fd, event in events:
            if event == select.EPOOLIN:
                active_list.append(fd, EV_READ)
            elif event == select.EPOOLOUT:
                active_list.append(fd, EV_WRITE)
        return active_list



class KqueueOp(object):

    def __init__(self):

        self.kqueuefd = select.kqueue()
        self.events = []


    def kqueue_add(self, fd, event_type):

        if event_type == EV_READ:
            event = select.kevent(fd, select.KQ_FILTER_READ,
                                  select.KQ_EV_ADD)
            self.events.append(event)
        elif event_type == EV_WRITE:
            event = select.kevent(fd, select.KQ_FILTER_WRITE,
                                  select.KQ_EV_ADD)
            self.events.append(event)


    def kqueue_del(self, fd, event_type):

        if event_type == EV_READ:
            event = select.kevent(fd, select.KQ_FILTER_READ,
                                  select.KQ_EV_ADD)
            self.events.remove(event)
        elif event_type == EV_WRITE:
            event = select.kevent(fd, select.KQ_FILTER_WRITE,
                                  select.KQ_EV_ADD)
            self.events.remove(event)


    def kqueue_dispatch(self, timeout):

        active_events = self.kqueuefd.control(self.events, len(self.events), timeout)

        active_list = []
        for event in active_events:
            if event.filter == select.KQ_FILTER_READ:
                active_list.append((event.ident, EV_READ))
            elif event.filter == select.KQ_FILTER_WRITE:
                active_list.append((event.ident, EV_WRITE))

        return active_list



class Event(object):

    def __init__(self, sock=None, ev_callback=None,
                 event_type=None, ev_arg=None):

        self.sock = sock
        self.ev_callback = ev_callback
        self.event_type = event_type
        self.ev_arg = ev_arg


    def set(self, sock, ev_callback, event_type, ev_arg):

        self.sock = sock
        self.ev_callback = ev_callback
        self.event_type = event_type
        self.ev_arg = ev_arg



class EventBase(object):

    def __init__(self):

        self.evsel = self.check_backend()
        self.events = {}
        self.active_list = []


    def check_backend(self):

        if platform.system() == 'Linux':
            backend = EpollOp()
        elif platform.system() == 'Darwin':
            backend = KqueueOp()
        else:
            backend = SelectOp()
        return backend


    def event_add(self, event):

        if event.sock.fileno() in self.events:
            return
        self.events[event.sock.fileno()] = event


    def event_del(self, event):

        if event.sock.fileno() not in self.events:
            raise ValueError("Don't have the event!")
        del self.events[event.sock.fileno()]


    def event_loop(self):
        
        while ()
