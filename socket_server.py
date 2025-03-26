from IPCutils import *

# Basic example - Inherit from BaseServer and let clients muck with some state
class MyServer(BaseServer):
    def __init__(self, host, port):
        # Super takes host addr, port, and max length of incoming connection
        # request queue
        super().__init__(host, port, 1)
        self.state = 0

    # Override handle_message
    def handle_message(self, client, msg):
        match msg:
            case _ if msg == STOP_SERVER_MSG:
              self.stop()
              self.tx_message(client, "Stopped")
              print("Stopped")
            case ("set", num):
              self.state = num
              self.tx_message(client, ("NewState", self.state))
              print(f"State: {self.state}")
            case ("add", num):
              self.state += num
              self.tx_message(client, ("NewState", self.state))
              print(f"State: {self.state}")
            case ("sub", num):
              self.state -= num
              self.tx_message(client, ("NewState", self.state))
              print(f"State: {self.state}")
            case _:
              print(f"Unknown Message: {msg}")

    def handle_connection(self, client):
       print("Someones connecting")
       return super().handle_connection(client)  

def main():
    s = MyServer('0.0.0.0', 9000)
    print("Server started. Listening for messages")

    while s.is_running():
        s.rx_message()

if __name__ == "__main__":
    main()