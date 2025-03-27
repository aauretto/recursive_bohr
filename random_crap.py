# Random Stuff that Aiden wanted to try cuz he thought it might be interesting.

from IPCutils import *
import threading

class myListener(BaseClient):
    def __init__(self):
        self.__super__().__init__()
    
    def handle_message(self, msg):
        match msg:
            case _ if msg == SERVER_STOPPING:
                self.disconnect()
                return False
            case ("State", state):
                print(state)
        return True
            
    def loop(self):
        while self.rx_message():
            pass

def launch_listener(host, port):
    l = myListener()
    l.connect_to(host, port)
    l.loop()

class mySpeaker(BaseClient):
    def __init__(self):
        self.__super__().__init__()
        self.allowedTokens = ["message", "list"]
        self.keepGoing = True
    
    def parse_input(self):
        s = input("Enter a message: ", end = "")
        match s.split():
            case ["send", msg]:
                self.tx_message(("message", msg))
            case ["lsit"]:
                self.tx_message(("list"))
            case ["stop"]:
                self.tx_message(STOP_SERVER_MSG)
                self.keepGoing = False
            case _:
                print(f"Unable tp parse input: {s}\nEnter a message: ", end = "")

    def loop(self):
        try:
            while self.keepGoing:
                self.parse_input()
                
        except KeyboardInterrupt:
            self.tx_message(STOP_SERVER_MSG)

def main():
    c = mySpeaker()
    c.connect_to("localhost, 9000")

if __name__ == "__main__":
    worker = threading.thread(target = launch_listener, args = ("localhost", 9000))
    
    worker.start()

    main()

    worker.join()