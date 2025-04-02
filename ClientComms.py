from IPCutils import *
from ClientState import *


class Client(BaseClient):
    def __init__(self, serverAddr, port, name):
        # When we call this, only input is on pygame screen
        super().__init__()
        
        # make connection and get start state
        self.connect_to(serverAddr, port)

        # Join game lobby and get initial state
        self.tx_message(("player-join", name))
        
        self.state = self.rx_message()
        

        self.state = None # Placeholder

    def handle_message(self, msg):
        match msg:
            case _ if msg == SERVER_STOPPING:
                self.keepGoing = False
            case ("initial-state", gameState):

            case ("new-state", gameState):
            
            case _:
                print(f"Unable to parse message: {msg}")

    ## Listener that just listens for messages and updates state



    ## Speaker that runs pygame and sends moves to server
    
