
import server
import event

if __name__ == "__main__":

    server_ip = ""
    server_port = 63333

    ev_base = event.EventBase()
    server.Server(server_ip, server_port, ev_base)

    ev_base.event_loop()