

import socket
import select
import platform
import time
import heapq


IO_READ = 0x01
IO_WRITE = 0x02


class SelectOp(object):

    def __init__(self):

        self.read_ev_set = []
        self.write_ev_set = []

    def ev_add(self, event):
        """add event to select backend

        """
        if event.io_type == IO_READ:
            self.read_ev_set.append(event.ev_fd)
        else:
            self.write_ev_set.append(event.ev_fd)

    def ev_del(self, event):
        """Delete event from select backend

        """
        if event.io_type == IO_READ:
            self.read_ev_set.remove(event)
        else:
            self.write_ev_set.remove(event)

    def ev_dispatch(self, timeout):
        """Select IO multiplexing

        """
        # we only focus on read/write event
        if timeout == -1:
            active_read_ev, active_write_ev, _ = \
                select.select(self.read_ev_set, self.write_ev_set, [])
        else:
            active_read_ev, active_write_ev, _ = \
                select.select(self.read_ev_set, self.write_ev_set, [], timeout)

        return (active_read_ev, active_write_ev)


class EpollOp(object):

    def __init__(self):

        self.epollfd = select.epoll()

    def ev_add(self, event):
        """Add event to epoll backend

        """
        if event.io_type == IO_READ:
            self.epollfd.register(event.ev_fd, select.EPOOLIN)
        else:
            self.epollfd.register(event.ev_fd, select.EPOOLOUT)

    def ev_del(self, event):
        """Delete event from epoll backend

        """
        self.epollfd.unregister(event.ev_fd)

    def ev_dispatch(self, timeout):
        """Epoll IO multiplexing

        """
        events = self.epollfd.epoll(timeout)

        active_read_ev = []
        active_write_ev = []
        for fd, event in events:
            if event & select.EPOOLIN:
                active_read_ev.append(fd)
            elif event & select.EPOOLOUT:
                active_write_ev.append(fd)
        return (active_read_ev, active_write_ev)


class KqueueOp(object):

    def __init__(self):

        self.kqueuefd = select.kqueue()
        self.fd_num = 0

    def _update_registration(self, fd, filter, op):
        """Private method for changing kqueue registration on a given
        file decriptor filtering for events given filter/op.

        """
        self.kqueuefd.control([select.kevent(fd, filter, op)], 0, 0)

    def ev_add(self, event):
        """Add event to Kqueue backend

        """
        if event.io_type == IO_READ:
            self._update_registration(event.ev_fd, select.KQ_FILTER_READ,
                                      select.KQ_EV_ADD)
        else:
            self._update_registration(event.ev_fd, select.KQ_FILTER_WRITE,
                                      select.KQ_EV_ADD)
        self.fd_num += 1

    def ev_del(self, event):
        """Delete event from Kqueue backend

        """
        if event.io_type == IO_READ:
            self._update_registration(event.ev_fd, select.KQ_FILTER_READ,
                                      select.KQ_EV_DELETE)
        else:
            self._update_registration(event.ev_fd, select.KQ_FILTER_WRITE,
                                      select.KQ_EV_DELETE)
        self.fd_num -= 1


    def ev_dispatch(self, timeout):
        """Kqueue IO multiplexing

        """
        timeout = None if timeout == -1 else timeout
        events = self.kqueuefd.control([], self.fd_num, timeout)

        active_read_ev = []
        active_write_ev = []
        for event in events:
            if event.filter == select.KQ_FILTER_READ:
                active_read_ev.append(event.ident)
            elif event.filter == select.KQ_FILTER_WRITE:
                active_write_ev.append(event.ident)
        return (active_read_ev, active_write_ev)


class Event(object):

    def __init__(self, fd, callback, arg):

        self.ev_fd = fd
        self.ev_callback = callback
        self.ev_arg = arg


class TimeEvent(Event):

    def __init__(self, call_back, arg, timeval):

        Event.__init__(self, -1, call_back, arg)
        self.ev_timeval = timeval


class IOEvent(Event):

    def __init__(self, fd, io_type, call_back, arg):

        Event.__init__(self, fd, call_back, arg)
        self.io_type = io_type


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

    def empty(self):

        return len(self._data) == 0

    def top(self):

        return self._data[0][1]


class EventBase(object):

    def __init__(self):

        self.evsel = self.check_backend()
        self.io_ev_map = {}
        self.time_ev_minheap = MinHeap(lambda time_event:
                                       time_event.ev_timeval)
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

        if isinstance(event, TimeEvent):
            # FOR time event
            self.time_ev_minheap.push(event)
        elif isinstance(event, IOEvent):
            if event.ev_fd in self.io_ev_map:
                self.io_ev_map[event.ev_fd].append(event)
            else:
                register_events = [event]
                self.io_ev_map[event.ev_fd] = register_events
            self.evsel.ev_add(event)

    def event_del(self, event):

        if isinstance(event, TimeEvent):
            pass
        elif isinstance(event, IOEvent):
            if event.ev_fd not in self.io_ev_map:
                return
            else:
                self.io_ev_map[event.ev_fd].remove(event)
            self.evsel.ev_del(event)

    def event_dispatch(self, timeout):
        """

        """
        active_read_ev, active_write_ev = \
                self.evsel.ev_dispatch(timeout)

        for fd in active_read_ev:
            for event in self.io_ev_map[fd]:
                if event.io_type == IO_READ:
                    self.active_io_ev.append(event)

        for fd in active_write_ev:
            for event in self.io_ev_map[fd]:
                if event.io_type == IO_WRITE:
                    self.active_io_ev.append(event)

    def timeout_next(self):

        if self.time_ev_minheap.empty():
            return -1
        else:
            now = time.time()
            event = self.time_ev_minheap.top()
            return event.ev_timeval - now

    def prepare_time_event(self):

        if self.time_ev_minheap.empty():
            return

        now = time.time()
        while self.time_ev_minheap.top().ev_timeval <= now:
            time_event = self.time_ev_minheap.pop()
            self.active_time_ev.append(time_event)

    def process_active_event(self):

        for time_event in self.active_time_ev:
            time_event.ev_callback(time_event.ev_arg)

        for io_event in self.active_io_ev:
            io_event.ev_callback(io_event.ev_arg)

    def event_loop(self):

        while True:

            timeout = self.timeout_next()

            self.event_dispatch(timeout)
            self.prepare_time_event()
            self.process_active_event()
