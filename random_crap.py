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
        print(f"\x1b[1F\x1b[L{msg.rstrip('\n')}\n", end="")
        print(f"-"*columns, end="") # should be on the old line - we can overwrite no issues here probably
        print(f"\x1b[u\n\x1b[u\x1b[1B", end="", flush=True)

def draw_prompt():
    with termLock:
        print(f"\x1b[1F\x1b[2K{PROMPT}",end = "")

class mySpeaker(BaseClient):
    def __init__(self):
        super().__init__()
        self.keepGoing = True
        self.listeners = []

    def parse_input(self):
        s = input()
        match s.split():
            case ["~kill-server"]:
                self.tx_message(STOP_SERVER_MSG)
                self.keepGoing = False
            case ["~done"]:
                self.tx_message(("im-leaving",))
                self.keepGoing = False
            case ["~rename", name]:
                self.tx_message(("rename", name))
            case ["~list"]:
                self.tx_message(("list",))
            case []:
                return
            case msg:
                self.tx_message(("message", " ".join(msg)))

    def handle_message(self, msg):
        match msg:
            case _ if msg == SERVER_STOPPING:
                self.keepGoing = False
            case ("writer-left",):
                return
            case ("status", msg):
                write_to_chatbox(f"\x1b[38;5;245m[SERVER] > {msg}\x1b[0m")
            case ("message", uname, msg):
                write_to_chatbox(f"[{uname}] > {msg}")
            case _:
                write_to_chatbox(f"\x1b[38;5;226m[Listener] --> UKN MSG: {msg}\x1b[0m")

    def make_listener(self):
        
        def loop():
            while self.keepGoing:
                self.rx_message()
        
        t = threading.Thread(target=loop)
        self.listeners.append(t)
        t.start()

    def cleanup(self):
        for t in self.listeners:
            t.join()

    def speaker_loop(self):
        try:
            while self.keepGoing:
                self.parse_input()
                draw_prompt()
        except KeyboardInterrupt:
            self.keepGoing = False
            self.tx_message(("im-leaving",))


def main():
    termLock = threading.Lock()

    c = mySpeaker()
    c.connect_to("10.243.100.155", 9000)

    columns = shutil.get_terminal_size().columns

    print("\x1b[38;5;245m[INFO] > Joined Room.\x1b[0m")
    print("-"*columns)
    print(PROMPT, end = "")

    c.make_listener()
    c.speaker_loop()
    c.cleanup()

    c.disconnect()


if __name__ == "__main__":
    main()