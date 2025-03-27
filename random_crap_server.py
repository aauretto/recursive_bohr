from IPCutils import *
import random
import string

# Basic example - Inherit from BaseServer and let clients muck with some state
class MyServer(BaseServer):
    def __init__(self, host, port):
        # Super takes host addr, port, and max length of incoming connection
        # request queue
        super().__init__(host, port, 1)
        self.unames = {}
        self.listeners = {}

    # Override handle_message
    def handle_message(self, client, msg):
        match msg:
            case _ if msg == STOP_SERVER_MSG:
              self.stop()
              self.tx_message(client, SERVER_STOPPING)
              print("Stopped")
            case ("message", msg):
              for listener in self.listeners:
                 self.tx_message(listener, self.unames[client], msg)
            case ("unreg-listener"):
              self.listeners.remove(client)
            case _:
              print(f"Unknown Message: {msg}")

    def random_string(length):
        chars = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
        return ''.join(random.choices(chars, k=length))

    def handle_connection(self, client):
       print("Someones connecting")
       [newClient] = super().handle_connection(client)
       self.unames[newClient] = f"No-Name-{newClient}"



def main():
    s = MyServer('localhost', 9000)
    print("Server started. Listening for messages")

    while s.is_running():
        s.rx_message()

if __name__ == "__main__":
    main()