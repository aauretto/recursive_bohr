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
            case ("initial-state", gameState): #TODO, do we assert that the typing is correct or just gracefully fail
                pass
            case ("new-state", gameState):
                pass
            case _:
                print(f"Unable to parse message: {msg}")
                # TODO do we gracefully exit here, what else would we do

    ## Listener that just listens for messages and updates state



    ## Speaker that runs pygame and sends moves to server
    
