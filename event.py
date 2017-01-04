

import socket
import select
import platform
import time
import heapq


EV_READ = 0x01
EV_WRITE = 0x02
EV_TIMEOUT = 0x04


class SelectOp(object):

    def __init__(self):

        self.read_set = []
        self.write_set = []


    def ev_add(self, event):

        if event.ev_type == EV_READ:
            self.read_set.append(event.ev_fd)
        elif event.ev_type == EV_WRITE:
            self.write_set.append(event.ev_fd)
        else:
            pass


    def ev_del(self, event):

        if event.ev_type == EV_READ:
            self.write_set.remove(event.ev_fd)
        elif event.ev_type == EV_WRITE:
            self.write_set.remove(event.ev_fd)
        else:
            # log
            pass


    def ev_dispatch(self, timeout):

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


    def ev_add(self, fd, event_type):

        if event_type & EV_READ:
            self.epollfd.register(fd, select.EPOOLIN)
        elif event_type & EV_WRITE:
            self.epollfd.register(fd, select.EPOOLOUT)
        else:
            #log
            raise UnknowType()


    def ev_del(self, fd, event_type):

        # TODO
        self.epollfd.unregister(fd)


    def ev_dispatch(self, timeout):

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


    def ev_add(self, fd, event_type):

        if event_type == EV_READ:
            event = select.kevent(fd, select.KQ_FILTER_READ,
                                  select.KQ_EV_ADD)
            self.events.append(event)
        elif event_type == EV_WRITE:
            event = select.kevent(fd, select.KQ_FILTER_WRITE,
                                  select.KQ_EV_ADD)
            self.events.append(event)


    def ev_del(self, fd, event_type):

        if event_type == EV_READ:
            event = select.kevent(fd, select.KQ_FILTER_READ,
                                  select.KQ_EV_ADD)
            self.events.remove(event)
        elif event_type == EV_WRITE:
            event = select.kevent(fd, select.KQ_FILTER_WRITE,
                                  select.KQ_EV_ADD)
            self.events.remove(event)


    def ev_dispatch(self, timeout):

        active_events = self.kqueuefd.control(self.events, len(self.events), timeout)

        active_list = []
        for event in active_events:
            if event.filter == select.KQ_FILTER_READ:
                active_list.append((event.ident, EV_READ))
            elif event.filter == select.KQ_FILTER_WRITE:
                active_list.append((event.ident, EV_WRITE))

        return active_list



class Event(object):

    def __init__(self, fd=None, sock=None,
                 ev_callback=None, event_type=None,
                 ev_arg=None, ev_timeout=-1):

        self.ev_fd = fd
        self.ev_sock = sock
        self.ev_callback = ev_callback
        self.ev_type = event_type
        self.ev_arg = ev_arg
        self.ev_timeout = ev_timeout



class MinHeap(object):

    def __init__(self, key=lambda x:x):

        self.key = key
        self._data = []


    def push(self, item):

        heapq.heappush(self._data, (self.key(item), item))


    def pop(self):

        try:
            return heapq.heappop(self._data)[1]
        except IndexError:
            return None

    
    def top(self):
        
        if self._data.empty():
            return None
        else:
            return self._data[0]



class EventBase(object):

    def __init__(self):

        self.evsel = self.check_backend()
        self.io_ev_map = {}
        self.time_ev_minheap = MinHeap(lambda event :
                                       event.ev_timeout)
        self.active_io_ev = []
        self.active_time_ev = []


    def check_backend(self):

        if platform.system() == 'Linux':
            # FOR Linux
            backend = EpollOp()
        elif platform.system() == 'Darwin':
            # FOR Mac OS
            backend = KqueueOp()
        else:
            # FOR Win
            backend = SelectOp()
        return backend


    def event_add(self, event):

        if event.type == EV_TIMEOUT:
            # FOR time event
            self.time_ev_minheap.push(event)
        elif event.fd not in self.io_ev_map:
            self.io_ev_map[event.fd] = event
            self.evsel.ev_add(event)
        else:
            pass


    def event_del(self, event):

        if event.fd not in self.io_ev_map:
            return

        self.evsel.ev_del(event)
        del self.io_ev_map[event.fd]

    
    def timeout_next(self):

        if self.time_ev_minheap.top() is None:
            return None
        else:
            now = time.time()
            event = self.time_ev_minheap.top()
            if now < event.ev_timeout:
                # something wrong
                pass
            else:
                return now - event.ev_timeout


    def event_loop(self):
        
        while (True):
            
            # Process Time Event
            timeout = self.timeout_next()

            if timeout is None:
                self.evsel.ev_dispatch()
