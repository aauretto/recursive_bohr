import time
from IPCutils import *
from SharedState import ClientState
import threading
from Display import Display
from queue import Queue
from enum import Enum



class Client(BaseClient):

    class ClientStatus(Enum):
        SETUP    = 0
        READYING = 1
        PLAYING  = 2

    def __init__(self, serverAddr, port, name, timeout=5):
        """
         Constructor for the Client class
 
         Parameters
         ----------
         serverAddr: str
             The IPv4 address of the server to connect to as a string
         port: int
             The port the server is running on
         name: str
             The name of the client
         timeout: int
             The time (seconds) to wait to connect to the server
 
         Returns
         -------
         : Client
         """
        
        # When we call this, only input is on pygame screen
        super().__init__()
        
        # Set timeout for connecting to the server
        self.sock.settimeout(timeout)
        
        ### Initialize members
        self.state = ClientState(None)
        self.name = name
        self.msgQueue = Queue()
        self.gameResult = None
        self.status = Client.ClientStatus.SETUP
        self.__keepGoing = True 

        self.display = Display(self.state, self.msgQueue)

        self.__spawn_listener(serverAddr, port)
        self.__spawn_sender()

        self.run()

    def run(self):
        """
        Runs the game
        """
        # Main Thread Handles Display
        self.display.run()
        self.__keepGoing = False

        self.sender.join()
        self.listener.join()
        
        if self.gameResult: # If we arent killed by user, show result
            self.display.final_state(self.gameResult)

    def __send_worker(self):
        """
        Worker that sends game action messages to the server.
        """
        while self.__keepGoing:
            msg = self.msgQueue.get(block=True)
            if msg:
                if not self.tx_message(msg) or msg == ("quitting",):
                    self.__keepGoing = False


    def __spawn_sender(self):
        """
        Spools up a sender thread
        """
        self.sender = threading.Thread(target=self.__send_worker)
        self.sender.start()

    def __listener_worker(self, serverAddr, port):
        """
        Loop for listener.
        Listens for messages and updates state when it gets one.
        """
        ### Set up socket:
        # make connection and get start state
        self.__keepGoing = self.connect_to(serverAddr, port)

        # Remove timeout for future communications
        self.sock.settimeout(None)
        
        if self.__keepGoing:
            while self.status == Client.ClientStatus.SETUP and self.__keepGoing:
                self.rx_message()
            print(f"Finished setup")
        else:
            # Kill display here and main thread will terminate
            self.display.stop_display()
            self.display.done_setup()
            raise UnableToConnectError(serverAddr, port)


        while self.__keepGoing:
            print(f"Listener looking for a message")
            self.rx_message()

    def __spawn_listener(self, serverAddr, port):
        """
        Spawns and starts the listener thread
        """
        self.listener = threading.Thread(target = self.__listener_worker, args = (serverAddr, port))
        self.listener.start()
        print("[DEBUG] > Created and started listener")


    def handle_message(self, msg):
        """
        Determines what the client should do upon recieving a message from the 
        server

        Parameters
        ----------
        msg: any
            The message received from the server

        Returns
        -------
        None
        """
        print(f"Client [{threading.get_ident()}] received {msg} | {self.status}")
        
        # Messages that should be handled the same regardless of client status
        match msg:
            case ("game-stopped", "player-left", who):
                    ## Go-go-gadget display stuff
                    self.stop_game()
                    print(f"{who} left the game. Closing...")
            case _:
                self.handle_state_specific_msg(msg)

    def handle_state_specific_msg(self, msg):        
        if self.status == Client.ClientStatus.SETUP:
            match msg:
                case ("ip-info", ip):
                    print(f"[Server] > Connected to {ip}")
                    print(f"[Server] > Waiting for opponent to join...")

                case ("name-request",):
                    self.msgQueue.put(("player-name", self.name))

                case ("all-names", players):
                    print(f"Everyone has joined. Players in lobby: {players}")
                    self.display.set_names(players)
                    self.status = Client.ClientStatus.READYING
                    # Should go through msgQueue
                    self.msgQueue.put(("ready",))
                case _:
                    print(f"Received message {msg} in SETUP phase")

        elif self.status == Client.ClientStatus.READYING:
            match msg:
                case ("state", "initial", csp): 
                    self.state.update_state(csp)
                    self.status = Client.ClientStatus.PLAYING
                    self.display.done_setup()
                    # Makeshift countdown
                    print("DEBUG > GOT INITIAL")
                    self.msgQueue.put(("no-animations",))
                case _:
                    print(f"Received message {msg} in READYING phase")
        elif self.status == Client.ClientStatus.PLAYING:
            match msg:
                case ("game-stopped", "draw", _):
                    self.gameResult = "draw"
                    self.stop_game()

                case ("game-stopped", "won", _):
                    self.gameResult = "won"
                    self.stop_game()

                case ("game-stopped", "lost", winner):
                    self.gameResult = "lost"
                    self.stop_game()

                case ("state", "new", csp): 
                    self.state.update_state(csp)

                case ("move", srcLayout, srcIdx, destLayout, destIdx): 
                    self.display.move_card(srcLayout, srcIdx, destLayout, destIdx, 0.5)

                case ("flip", cards, pileIdxs): 
                    self.display.flip_cards(cards, pileIdxs, 1)


                    ### Go-go-gadget display stuff
                case _:
                    print(f"Unable to parse message: {msg} while PLAYING")
                    # TODO do we gracefully exit here, what else would we do
        else:
            print(f"Print in bad Client state while receiving {msg}")

    def stop_game(self):
        """
        TODO make this better / get rid
        """
        time.sleep(0.050) # give pygame time to refresh last move #TODO KILL
        self.__keepGoing = False
        self.display.stop_display() 

if __name__ == "__main__":
    print("RUNNING CODE (WATCH OUT)")   
    name = input('Player Name: ')
    # myCli = Client("10.0.0.249", 9000, name)
    myCli = Client("localhost", 9000, name)
