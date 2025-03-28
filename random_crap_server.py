from IPCutils import *
import random
import string

# Basic chat server example -- Going to see if we can split the socket on the
# client side and have one thread listen while another makes transmissions
class MyServer(BaseServer):
    def __init__(self, host, port):
        # Super takes host addr, port, and max length of incoming connection
        # request queue
        super().__init__(host, port, 1)
        self.unames = {}
        self.gid = 0
    # Override handle_message
    def handle_message(self, client, msg):
        match msg:
            case _ if msg == STOP_SERVER_MSG:
              self.stop()
              self.tx_message(client, SERVER_STOPPING)
              print("Stopped")
            case ("message", msg):
                 self.broadcast_message(("message", self.unames[client], msg))
            case ("rename", newName):
                 self.unames[client] = newName
                 self.tx_message(client, ("message", "SERVER", f"Your name is now {newName}"))
            case ("im-leaving",):
                print(f"{self.unames[client]} left.")
                self.tx_message(client, ("writer-left",))
            case _:
              print(f"Unknown Message: {msg}")

    def handle_connection(self):
       print("Someones connecting")
       [newClient] = self.accept_connections()
       self.unames[newClient] = f"No-Name-{self.gid}"
       self.gid += 1

def main():
    s = MyServer('localhost', 9000)
    print("Server started. Listening for messages")

    while s.is_running():
        s.rx_message()

if __name__ == "__main__":
    main()