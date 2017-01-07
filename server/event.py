


import select
import platform
import time
import heapq


EV_IO_READ = 0x01
EV_IO_WRITE = 0x02

EV_READABLE = 0x01
EV_WRITABLE = 0x02

EV_TYPE_ADD = 0x01
EV_TYPE_DEL = 0x02


class EventError(Exception):
    """Event Error
    """
    pass


class Event(object):

    def __init__(self, fd):

        self.ev_fd = fd

    def call_back(self):
        """call_back function, need to override

        """
        pass


class TimeEvent(Event):

    def __init__(self, timeval):

        Event.__init__(self, -1)
        self.ev_timeval = timeval


class IOEvent(Event):

    def __init__(self, fd):

        Event.__init__(self, fd)
        self.io_type = 0x00
        self.io_res = 0x00

    def get_io_type(self):
        """Get event io type

        """
        return self.io_type

    def set_io_type(self, io_type):
        """Set event io type

        """
        self.io_type = io_type

    def get_io_res(self):

        return self.io_res

    def set_io_res(self, io_res):

        self.io_res |= (io_res)

    def clear_io_res(self, io_res):

        self.io_res &= ~(io_res)

    def call_back(self):

        if self.get_io_res() & EV_READABLE:
            self.read()
            self.clear_io_res(EV_READABLE)

        if self.get_io_res() & EV_WRITABLE:
            self.write()
            self.clear_io_res(EV_WRITABLE)

    def read(self):
        """FOR read event, need to override

        """
        pass

    def write(self):
        """FOR write event, need to override

        """
        pass


class SelectOp(object):

    def __init__(self):

        self.read_ev_set = []
        self.write_ev_set = []

    def ev_add(self, event):
        """add event to select backend

        """
        if event.io_type & EV_IO_READ:
            self.read_ev_set.append(event.ev_fd)

        if event.io_type & EV_IO_WRITE:
            self.write_ev_set.append(event.ev_fd)


    def ev_del(self, event):
        """Delete event from select backend

        """
        if event.io_type & EV_IO_READ:
            self.read_ev_set.remove(event.fd)

        if event.io_type & EV_IO_WRITE:
            self.write_ev_set.remove(event.fd)

    def ev_set(self, old_event, new_event):
        """Set new io type for event

        """
        self.ev_del(old_event)
        self.ev_add(new_event)

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
        if event.io_type & EV_IO_READ:
            self.epollfd.register(event.ev_fd, select.EPOOLIN)

        if event.io_type & EV_IO_WRITE:
            self.epollfd.register(event.ev_fd, select.EPOOLOUT)

    def ev_del(self, event):
        """Delete event from epoll backend

        """
        self.epollfd.unregister(event.ev_fd)

    def ev_set(self, old_event, new_event):
        """Set new io type for event

        """
        self.ev_del(old_event)
        self.ev_add(new_event)

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
        if event.io_type & EV_IO_READ:
            self._update_registration(event.ev_fd, select.KQ_FILTER_READ,
                                      select.KQ_EV_ADD)
        if event.io_type & EV_IO_WRITE:
            self._update_registration(event.ev_fd, select.KQ_FILTER_WRITE,
                                      select.KQ_EV_ADD)
        self.fd_num += 1

    def ev_del(self, event):
        """Delete event from Kqueue backend

        """
        if event.io_type & EV_IO_READ:
            self._update_registration(event.ev_fd, select.KQ_FILTER_READ,
                                      select.KQ_EV_DELETE)
        if event.io_type & EV_IO_WRITE:
            self._update_registration(event.ev_fd, select.KQ_FILTER_WRITE,
                                      select.KQ_EV_DELETE)
        self.fd_num -= 1

    def ev_set(self, old_event, new_event):

        self.ev_del(old_event)
        self.ev_add(new_event)

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

        self.evsel = self._check_backend()
        self.io_ev_map = {}
        self.time_ev_minheap = MinHeap(lambda time_event:
                                       time_event.ev_timeval)
        self.active_io_ev = {}
        self.active_time_ev = []

    def _check_backend(self):
        """Check Environment, select IO multiplexing backend.

        """
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

    def has_event(self, ev_fd):

        return ev_fd in self.io_ev_map

    def set_event(self, ev_fd, io_type):
        """Set event io type and register to IO multiplexing reactor

        """
        old_event = self.io_ev_map[ev_fd]
        self.io_ev_map[ev_fd].set_io_type(io_type)
        self.evsel.ev_set(old_event, self.io_ev_map[ev_fd])

    def add_event(self, event):
        """

        """
        if isinstance(event, TimeEvent):
            # FOR time event
            self.time_ev_minheap.push(event)
        else:
            self.io_ev_map[event.ev_fd] = event
        self.evsel.ev_add(event)

    def del_event(self, event):
        """

        """
        if isinstance(event, TimeEvent):
            pass
        else:
            del self.io_ev_map[event.ev_fd]
        self.evsel.ev_del(event)

    def _dispatch_event(self, timeout):
        """

        """
        active_read_ev, active_write_ev = \
                self.evsel.ev_dispatch(timeout)

        for fd in active_read_ev:

            self.io_ev_map[fd].set_io_res(EV_READABLE)
            if fd not in self.active_io_ev:
                self.active_io_ev[fd] = self.io_ev_map[fd]

        for fd in active_write_ev:

            self.io_ev_map[fd].set_io_res(EV_WRITABLE)
            if fd not in self.active_io_ev:
                self.active_io_ev[fd] = self.io_ev_map[fd]

    def _timeout_next(self):

        if self.time_ev_minheap.empty():
            return -1
        else:
            now = time.time()
            event = self.time_ev_minheap.top()
            return event.ev_timeval - now

    def _prepare_time_event(self):

        if self.time_ev_minheap.empty():
            return

        now = time.time()
        while self.time_ev_minheap.top().ev_timeval <= now:
            time_event = self.time_ev_minheap.pop()
            self.active_time_ev.append(time_event)

    def _process_active_event(self):

        for time_event in self.active_time_ev:
            time_event.call_back()

        for _, event in self.active_io_ev.iteritems():
            event.call_back()

    def event_loop(self):

        while True:

            timeout = self._timeout_next()

            self._dispatch_event(timeout)
            self._prepare_time_event()
            self._process_active_event()
