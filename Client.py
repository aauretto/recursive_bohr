import time
from IPCutils import *
from SharedState import ClientState
import threading
from Display import Display
from queue import Queue
from enum import Enum
from threading import Lock



class Client(BaseClient):

    class ClientStatusValue(Enum):
        SETUP    = 0
        READYING = 1
        PLAYING  = 2
        STOPPING = 3

    class ClientStatus():
        def __init__(self):
            """
            Constructor for ClientStatus, a monitored status indicator.
            """
            self.__status = Client.ClientStatusValue.SETUP
            self.__lock = Lock()

        def update_status(self, value):
            """
            Update status if not already STOPPING 

            Parameters
            ----------
            value: Client.ClientStatusValue
                New status
            
            Returns
            -------
            None
            """
            with self.__lock:
                if self.__status != Client.ClientStatusValue.STOPPING:
                    self.__status = value

        def get_status(self):
            """
            Get current status 

            Returns
            -------
            : Client.ClientStatusValue
            """
            with self.__lock:
                return self.__status
            




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
        self.__state = ClientState(None)
        self.__name = name
        self.__msgQueue = Queue()
        self.__gameResult = None
        self.__status = Client.ClientStatus()

        self.__display = Display(self.__state, self.__msgQueue)

        self.__spawn_listener(serverAddr, port)
        self.__spawn_sender()

        self.run()

    def run(self):
        """
        Runs the game
        """
        # Main Thread Handles Display
        self.__display.run()
        self.__status.update_status(Client.ClientStatusValue.STOPPING)
        
        # Wait for the sender and listener to finish
        self.__sender.join()
        self.__listener.join()
        
        if self.__gameResult: # If we arent killed by user, show result
            self.__display.final_state(self.__gameResult)

    def __send_worker(self):
        """
        Worker that sends game action messages to the server.
        """
        while self.__status.get_status() != Client.ClientStatusValue.STOPPING:
            msg = self.__msgQueue.get(block=True)
            # Falsey values used as sentinels
            if msg:
                if not self.tx_message(msg) or msg == ("quitting",):
                    self.__status.update_status(Client.ClientStatusValue.STOPPING)


    def __spawn_sender(self):
        """
        Spools up a sender thread
        """
        self.__sender = threading.Thread(target=self.__send_worker)
        self.__sender.start()

    def __listener_worker(self, serverAddr, port):
        """
        Loop for listener.
        Listens for messages and updates state when it gets one.
        """
        ### Set up socket:
        # make connection and get start state
        if not self.connect_to(serverAddr, port):
            self.__status.update_status(Client.ClientStatusValue.STOPPING)

        # Remove timeout for future communications
        self.sock.settimeout(None)
        
        if self.__status.get_status() == Client.ClientStatusValue.STOPPING:
            # Kill display here and main thread will terminate
            self.__display.stop_display()
            self.__msgQueue.put(None) 
            raise UnableToConnectError(serverAddr, port) #TODO consider that this does not actually error ???

        # Receive messages until the we are done
        while self.__status.get_status() != Client.ClientStatusValue.STOPPING:
            self.rx_message()

    def __spawn_listener(self, serverAddr, port):
        """
        Spawns and starts the listener thread
        """
        self.__listener = threading.Thread(target = self.__listener_worker, args = (serverAddr, port))
        self.__listener.start()
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
        # Messages that should be handled the same regardless of client status
        match msg:
            case ("game-stopped", "player-left", who):
                    self.stop_game()
                    print(f"{who} left the game. Closing...")
            case _:
                self.handle_state_specific_msg(msg)

    def handle_state_specific_msg(self, msg):      
        """
        Handles a message that only is applicable when in a certain state

        Parameters
        ----------
        msg: any
            The received message
        
        Returns
        -------
        None
        """  
        if self.__status.get_status() == Client.ClientStatusValue.SETUP:
            match msg:
                case ("ip-info", ip):
                    print(f"[Server] > Connected to {ip}")
                    print(f"[Server] > Waiting for opponent to join...")

                case ("name-request",):
                    self.__msgQueue.put(("player-name", self.__name))

                case ("all-names", players):
                    print(f"Everyone has joined. Players in lobby: {players}")
                    self.__display.set_names(players)
                    self.__status.update_status(Client.ClientStatusValue.READYING)
                    # Should go through msgQueue
                    self.__msgQueue.put(("ready",))
                case _:
                    print(f"Received message {msg} in SETUP phase")

        elif self.__status.get_status() == Client.ClientStatusValue.READYING:
            match msg:
                case ("state", "initial", csp): 
                    self.__state.update_state(csp)
                    self.__display.set_initial()
                    self.__status.update_status(Client.ClientStatusValue.PLAYING)
                    self.__display.done_setup()

                case _:
                    print(f"Received message {msg} in READYING phase")

        elif self.__status.get_status() == Client.ClientStatusValue.PLAYING:
            match msg:
                case ("game-stopped", "draw", _):
                    self.__gameResult = "draw"
                    self.stop_game()

                case ("game-stopped", "won", _):
                    self.__gameResult = "won"
                    self.stop_game()

                case ("game-stopped", "lost", winner):
                    self.__gameResult = "lost"
                    self.stop_game()

                case ("state", "new", csp): 
                    self.__state.update_state(csp)

                case ("move", srcLayout, srcIdx, destLayout, destIdx): 
                    self.__display.move_card(srcLayout, srcIdx, destLayout, destIdx, 0.5)

                case ("flip", cards, pileIdxs): 
                    self.__display.flip_cards(cards, pileIdxs, 1)
                
                case ("bad-move", _, pileIdx):
                    self.__display.bad_move(pileIdx)


                case _:
                    print(f"Unable to parse message: {msg} while PLAYING")
        else:
            print(f"Print in bad Client state while receiving {msg}")

    def stop_game(self):
        """
        Set client status to stopping and gracefully stop the display
        """
        self.__status.update_status(Client.ClientStatusValue.STOPPING)
        self.__display.stop_display() 
        self.__msgQueue.put(None) 

if __name__ == "__main__":
    ip = input("Enter the IP to connect to: ")   
    port = int(input("Enter the port to connect to: "))   
    
    name = input('Player Name: ')
    myCli = Client(ip, port, name)