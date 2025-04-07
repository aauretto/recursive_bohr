from IPCutils import *
from SharedState import ClientState
import threading
from Display import Display
from queue import Queue


class Client(BaseClient):
    def __init__(self, serverAddr, port, name, timeout=5):
        # When we call this, only input is on pygame screen
        super().__init__()
        # Set timeout for connecting to the server
        self.sock.settimeout(timeout)
        
        ### Initialize members
        self.state = ClientState(None)
        self.name = name
        self.msgQueue = Queue()

        ### Set up socket:
        # make connection and get start state
        self.__keepGoing = self.connect_to(serverAddr, port)

        # Remove timeout for future communications
        self.sock.settimeout(None)

        if self.__keepGoing:
            self.display = Display(self.state, self.msgQueue)
            self.__setup()
            print(f"Finished setup")
        else:
            raise UnableToConnectError(serverAddr, port)
        
        self.run()

    def run(self):
        self.display.run()
        self.keepGoing = False
        self.sender.join()
        self.listener.join()
    
    def __setup(self):
        # Join game lobby and get initial state
        self.__spawn_sender()
        
        while not self.state.has_data():
            self.rx_message()
        print(f'State received')
        self.__spawn_listener()

    def __send_worker(self):
        """
        Worker that sends game action messages to the server.
        """
        while self.__keepGoing:
            msg = self.msgQueue.get(block=True)
            self.tx_message(msg)

    def __spawn_sender(self):
        """
        Spools up a sender thread
        """
        self.sender = threading.Thread(target=self.__send_worker)
        self.sender.start()

    def __listener_worker(self):
        """
        Loop for listener.
        Listens for messages and updates state when it gets one.
        """
        while self.__keepGoing:
            self.rx_message()

    def __spawn_listener(self):
        self.listener = threading.Thread(target = self.__listener_worker)
        self.listener.start()


    def handle_message(self, msg):
        print(f"Client received {msg}")
        match msg:
            case ("game-stopped", "player-left", who):
                ## Go-go-gadget display stuff
                self.keepGoing = False
            case ("state", tag, csp): 
                self.state.update_state(csp)
            case ("name-request",):
                self.tx_message(("player-name", self.name))
            case ("everybody-joined", players):
                self.display.get_ready(players)
                ## Go-go-gadget display stuff
            case _:
                print(f"Unable to parse message: {msg}")
                # TODO do we gracefully exit here, what else would we do

if __name__ == "__main__":
    print("RUNNING CODE (WATCH OUT)")   
    name = input('Player Name: ')
    myCli = Client("localhost", 9000, name)
