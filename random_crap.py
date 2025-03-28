# Random Stuff that Aiden wanted to try cuz he thought it might be interesting.

from IPCutils import *
import threading
import shutil

PROMPT = " >>> "
termLock = threading.Lock()


# THIS AND DRAW_PROMPT ARE EXTRA STUFF I TRIED
def write_to_chatbox(msg):
    with termLock:
        columns = shutil.get_terminal_size().columns
        print(f"\x1b[s",end="")
        print(f"\x1b[1F\x1b[L{msg.rstrip("\n")}\n", end="")
        print(f"-"*columns, end="") # should be on the old line - we can overwrite no issues here probably
        print(f"\x1b[u\n\x1b[u\x1b[1B", end="", flush=True)

def draw_prompt():
    with termLock:
        print(f"\x1b[1F\x1b[2K{PROMPT}",end = "")


class myListener(BaseClient):
    def __init__(self):
        super().__init__()

    def handle_message(self, msg):
        match msg:
            case _ if msg == SERVER_STOPPING:
                return False
            case ("writer-left",):
                return False
            case ("message", uname, msg):
                write_to_chatbox(f"[{uname}] > {msg}")
            case _:
                write_to_chatbox(f"[Listener] --> UKN MSG: {msg}")
        return True

    def loop(self):
        while self.rx_message():
            pass

    # Give this an already opened socket and it will listen to it
    def listen_to(self, sock):
        self.disconnect()
        self.sock = sock

class mySpeaker(BaseClient):
    def __init__(self):
        super().__init__()
        self.keepGoing = True
    
    def parse_input(self):
        s = input()
        match s.split():
            case ["kill-server"]:
                self.tx_message(STOP_SERVER_MSG)
                self.keepGoing = False
            case ["done"]:
                self.tx_message(("im-leaving",))
                self.keepGoing = False
            case ["rename", name]:
                self.tx_message(("rename", name))
            case []:
                return
            case msg:
                self.tx_message(("message", " ".join(msg)))

    def get_sock(self):
        return self.sock

    def loop(self):
        try:
            while self.keepGoing:
                self.parse_input()
                draw_prompt()
                
        except KeyboardInterrupt:
            self.tx_message(("im-leaving",))


def listen_and_print(sock):
    l = myListener()
    l.listen_to(sock)
    l.loop()

def main():
    termLock = threading.Lock()

    c = mySpeaker()
    c.connect_to("localhost", 9000)

    columns = shutil.get_terminal_size().columns

    print("\x1b[2m[INFO] > Joined Room.\x1b[0m")
    print("-"*columns)
    print(PROMPT, end = "")

    worker = threading.Thread(target = listen_and_print, args = (c.get_sock(),))
    worker.start()
    c.loop()
    worker.join()
    c.disconnect()


if __name__ == "__main__":
    main()