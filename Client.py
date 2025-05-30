"""
File: Client.py
Authors: Aiden Auretto, Peter Scully, Simon Webber, Claire Williams
Date: 4/28/2025

Purpose
------- 
    Contains the main for Client side code and the Client class which
    drives the Client code
"""
from IPCutils import *
from SharedState import ClientState
import threading
from Display import Display
from queue import Queue
from enum import Enum
from threading import Lock



class Client(BaseClient):

    class ClientStatusValue(Enum):
        """
        The possible statuses the Client can have
        """
        SETUP    = 0
        READYING = 1
        PLAYING  = 2
        STOPPING = 3

    class ClientStatus():
        """
        A monitor for ClientStatusValue to synchronize access across threads
        and ensure it cannot be unstopped
        """
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

    #*********************************************************************#
    #          Constructor and Driver function for the Client             #
    #*********************************************************************#
    
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
        self._sock.settimeout(timeout)
        
        ### Initialize members
        self.__state = ClientState(None)
        self.__name = name
        self.__msgQueue = Queue()
        self.__gameResult = None
        self.__status = Client.ClientStatus()

        self.__display = Display(self.__state, self.__msgQueue)

        self.__spawn_listener(serverAddr, port)
        self.__spawn_sender()


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

    #*********************************************************************#
    #       Internal functions for the sender and listener threads        #
    #*********************************************************************#

    def __send_worker(self):
        """
        Worker that sends game action messages to the server.
        """
        while self.__status.get_status() != Client.ClientStatusValue.STOPPING:
            msg = self.__msgQueue.get(block=True)
            # Falsey values used as sentinels
            if msg:
                if not self.tx_message(msg) or msg == ("quitting",):
                    self.__status.update_status(
                        Client.ClientStatusValue.STOPPING)

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
        self._sock.settimeout(None)
        
        if self.__status.get_status() == Client.ClientStatusValue.STOPPING:
            # Kill display here and main thread will terminate
            self.__display.stop_display()
            self.__msgQueue.put(None) 
            raise UnableToConnectError(serverAddr, port)

        # Receive messages until the we are done
        while self.__status.get_status() != Client.ClientStatusValue.STOPPING:
            self.rx_message()

    def __spawn_listener(self, serverAddr, port):
        """
        Spawns and starts the listener thread
        """
        self.__listener = threading.Thread(target = self.__listener_worker, 
                                           args = (serverAddr, port))
        self.__listener.start()

    #*********************************************************************#
    #      Functions for handling incomming messages from the server      #
    #*********************************************************************#

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
        match msg:
            # Messages that should be handled the same regardless of client 
            # status
            case ("game-stopped", "player-left", who):
                    self.__stop_game()
                    print(f"{who} left the game. Closing...")
            case ("game-stopped", "server-killed", _):
                    self.__stop_game()
                    print(f"Server dies. Closing...")
            case _:
                if self.__status.get_status() == Client.ClientStatusValue.SETUP:
                    self.__handle_setup_message(msg)
                    
                elif self.__status.get_status() == \
                    Client.ClientStatusValue.READYING:
                    self.__handle_readying_message(msg)

                elif self.__status.get_status() == \
                    Client.ClientStatusValue.PLAYING:
                    self.__handle_playing_message(msg)

                else:
                    print(f"In bad Client state while receiving {msg}")

    def __handle_setup_message(self, msg):
        """
        Handles a message intended only for the setup state

        Parameters
        ----------
        msg: any
            The received message
        
        Returns
        -------
        None
        """ 
        match msg:
            case ("ip-info", ip):
                print(f"[Server] > Connected to {ip}")
                print(f"[Server] > Waiting for opponent to join...")

            case ("name-request",):
                self.__msgQueue.put(("player-name", self.__name))

            case ("all-names", players):
                self.__display.set_names(players)
                self.__status.update_status(Client.ClientStatusValue.READYING)
                # Should go through msgQueue
                self.__msgQueue.put(("ready",))
            case _:
                print(f"Received bad message {msg} in SETUP phase")

    def __handle_readying_message(self, msg):
        """
        Handles a message intended only 

        Parameters
        ----------
        msg: any
            The received message
        
        Returns
        -------
        None
        """ 
        match msg:
            case ("state", "initial", csp): 
                self.__state.update_state(csp)
                self.__display.set_initial()
                self.__status.update_status(Client.ClientStatusValue.PLAYING)
                self.__display.done_setup()

            case _:
                print(f"Received bad message {msg} in READYING phase")

    def __handle_playing_message(self, msg):
        """
        Handles a message intended for the playing phase

        Parameters
        ----------
        msg: any
            The received message
        
        Returns
        -------
        None
        """ 
        match msg:
            case ("game-stopped", result, _):
                self.__gameResult = result
                self.__msgQueue.put(('got-result',))
                self.__stop_game()

            case ("state", "new", csp): 
                self.__state.update_state(csp)

            case ("move", srcLayout, srcIdx, destLayout, destIdx): 
                self.__display.move_card(srcLayout, srcIdx, destLayout, 
                                         destIdx, 0.5)

            case ("flip", cards, pileIdxs): 
                self.__display.flip_cards(cards, pileIdxs, 1)
            
            case ("bad-move", _, pileIdx):
                self.__display.bad_move(pileIdx)

            case _:
                print(f"Received bad message {msg} in PLAYING phase")
             

    #*********************************************************************#
    #         Function for gracefully ending the game and closing         #
    #*********************************************************************#
    def __stop_game(self):
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
    myCli.run()