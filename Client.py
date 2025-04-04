from IPCutils import *
from ClientState import *
import threading
import time

class Client(BaseClient):
    def __init__(self, serverAddr, port, name, timeout=5):
        # When we call this, only input is on pygame screen
        super().__init__()
        # Set timeout for connecting to the server
        self.sock.settimeout(timeout)
        
        ### Initialize members
        self.state = None
        self.name = name

        ### Set up socket:
        # make connection and get start state
        self.__keepGoing = self.connect_to(serverAddr, port)

        # Remove timeout for future communications
        self.sock.settimeout(None)

        if self.__keepGoing:
            self.__setup()
            self.__display_loop()
        else:
            raise UnableToConnectError(serverAddr, port)
        

    def __display_loop(self):
        while self.__keepGoing:
            # DO display stuff in here
            (m, t, mid) = self.state.get_state()

            print(*t, sep = " | ")
            print(*mid, sep = "     ")
            print(*m, sep = " | ")

            layoutIdx, midPileIdx = self.TEMP_parse_cli()
            self.tx_message(("play", layoutIdx, midPileIdx))

    def TEMP_parse_cli(self):
        [layoutStr, midStr] = input("Input: ").split()  
        return (int(layoutStr), int(midStr))

    def __setup(self):
        # Join game lobby and get initial state

        while not self.state:
            self.rx_message()
        self.__spawn_listener()

        

    def __listener_worker(self):
        """
        Loop for listener.
        Listens for messages and updates state when it gets one.
        """
        while self.__keepGoing:
            self.rx_message()


    def __spawn_listener(self):
        self.worker = threading.Thread(target = self.__listener_worker)
        self.worker.start()


    def handle_message(self, msg):
        match msg:
            case ("game-stopped", "player-left", who):
                ## Go-go-gadget display stuff
                self.keepGoing = False
            case ("state", tag, csp): 
                self.state = ClientState(csp)
            case ("name-request",):
                self.tx_message(("player-name", self.name))
                self.tx_message(("ready",))
            case ("everybody-joined", players):
                print(f"Players in session: {players}")
                ## Go-go-gadget display stuff
            case _:
                print(f"Unable to parse message: {msg}")
                # TODO do we gracefully exit here, what else would we do

if __name__ == "__main__":
    print("RUNNING CODE (WATCH OUT)")   
    name = input('Player Name: ')
    myCli = Client("localhost", 9000, name)
