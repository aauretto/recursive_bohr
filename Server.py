from IPCutils import *
from ServerGameState import *
from enum import Enum
from functools import *
from SharedState import ClientStatePackage, PlayCardAction
import socket

class Server(BaseServer):
    class ClientStatus(Enum):
        """
        Description of the possible status the connected clients can have
        """
        CONNECTED = 0
        READY     = 1
        PLAYING   = 2 

    class ServerStatus(Enum):
        """
        Description of the possible status the server can have
        """
        SETUP   = 0
        RUNNING = 1
        STOPPING = 2
    
    #*********************************************************************#
    #           Constructor and Driver functions for the Server           #
    #*********************************************************************#
    def __init__(self, host, port, numPlayers=2, numGamePiles=2, layoutSize=4):
        """
        Constructor for the Server class

        Parameters
        ----------
        host: str
            The IPv4 address the server is running on
        port: int
            The port number the server will run on
        numPlayers: int
            the number of players in the game, Default is 2
        numGamePiles: int
            The number of center piles in the game
        layoutSize: int
            The number of layout piles per player

        Notes
        -----
        Changes to the default parameters are not handled throughout the
        codebase. Change at your own risk
        """
        # Super takes host addr, port, and max length of incoming connection
        # request queue
        super().__init__(host, port, numPlayers)
        # Maps clients to idx for checking moves in state
        self.__currentPlayers = {}
        self.__maxPlayers = numPlayers
        self.__serverStatus = Server.ServerStatus.SETUP

        self.__state = ServerGameState(numPlayers=numPlayers, 
                                     numGamePiles=numGamePiles, 
                                     layoutSize=layoutSize)

    def start(self):
        """
        Starts up the server and run the game
        """
        while self.__serverStatus == Server.ServerStatus.SETUP:
            self.rx_message()

        # When we're done with SETUP, keep going if we are RUNNING
        if self.__serverStatus == Server.ServerStatus.RUNNING:
            for client in self.__currentPlayers.keys():
                self.__currentPlayers[client]['status'] = Server.ClientStatus.PLAYING
            
            # Give everyone the initial gamestate
            self.__broadcast_gamestate('initial')   

            # Begin the game
            self.__loop()

    def __loop(self):
        """
        Runs the game
        """
        ### TODO SOCKET TIMEOUT THINS
        print(f"Loop start status = {self.__serverStatus}")
        while self.__serverStatus == Server.ServerStatus.RUNNING:
            self.rx_message()

    #*********************************************************************#
    #                    Synchronizers for flip event                     #
    #*********************************************************************#   

    def __flip_if_able(self):
        """
        Initiates flipping if it is a legitimate time to do so

        Returns
        -------
        : bool
            An indicator of whether or not a flip occured or nor
        """
        # Only flip if no one is currently animating and no one can do anything
        if not self.__any_animating() and not self.__state.moves_available():
            
            playersFlipped = self.__state.flip()
            cardsToFlip = [c for (i, c) in enumerate(self.__state.get_game_piles()) if i in playersFlipped]

            self.broadcast_message(("flip", cardsToFlip, playersFlipped))
            self.__broadcast_gamestate("new")
            self.__make_all_animating()
            return True
        return False

    def __make_all_animating(self):
        """
        Sets all the players to be animating
        """
        for v in self.__currentPlayers.values():
            v['animating'] = True

    #*********************************************************************#
    #       Functions and helpers for sending and recieving messages      #
    #*********************************************************************#

    def handle_message(self, client, msg):
            """
            Handles what the server should do upon recieving a given message

            Parameters
            ----------
            client: socket.socket
                The socket of the client who sent the msg
            msg: any
                The message recieved from the client

            """
            #TODO make a handle state specific message
            if self.__serverStatus == Server.ServerStatus.SETUP:
                # We only want to handle these types of messages in the SETUP phase
                match msg:
                    case ("player-name", name):
                        self.__currentPlayers[client]["uname"] = name
                        if self.__all_named():
                            self.broadcast_message(("all-names", self.__player_names()))
                    case ("ready",):
                        self.__currentPlayers[client]['status'] = Server.ClientStatus.READY
                        if self.__all_ready():
                            print("Setting status to running")
                            self.__serverStatus = Server.ServerStatus.RUNNING
                    case ("quitting",):
                        self.__stop_game("player-left", self.__currentPlayers[client]['uname'])
                    case _:
                        print(f"Received message {msg} in SETUP phase")
        
            elif self.__serverStatus == Server.ServerStatus.RUNNING:
                # Handle these messages while the game is running
                match msg:
                    case ("play", playAction):    
                        self.__handle_play(client, playAction)
                    case ("quitting",):
                        self.__stop_game("player-left", self.__currentPlayers[client]['uname'])
                    case ("done-moving",):
                        self.__currentPlayers[client]['animating'] = False
                        (gameOver, winnerId) = self.__state.game_over()
                        if gameOver:
                            self.__terminate_game(winnerId)
                        else:
                            self.__flip_if_able()

    def __handle_play(self, client, playAction):
            """
            Handles when a client attempts to take an action

            Parameters
            ----------
            client: socket.socket
                The socket of the client attempting the move
            playAction: PlayCardAction
                The move attempted by the player
            """
            # Get the client idx and attempt the move
            clientIdx = self.__currentPlayers[client]["id"]
            validMove = self.__state.play_card(clientIdx, 
                                                playAction.layoutIdx, 
                                                playAction.midPileIdx)
            
            # If the move is allowed we send the new gamestate back to everyone
            if validMove:
                self.exclusive_broadcast([client], ("move", "them", playAction.layoutIdx, "mid", playAction.midPileIdx))
                self.tx_message(client, ("move", "me", playAction.layoutIdx, "mid", playAction.midPileIdx))
                self.__broadcast_gamestate("new")
                self.__currentPlayers[client]['animating'] = True
            else:
                # Otherwise we tell the client they made a bad move
                self.tx_message(client, 
                                ("bad-move", 
                                playAction.layoutIdx, 
                                playAction.midPileIdx))

    def handle_connection(self):
            """
            Handles a new connection to the server
            """
            # If the game is full, reject new connections
            if len(self.__currentPlayers) >= self.__maxPlayers:
                self.reject_connections()
            else:
                # Otherwise accept the new connections and initialize them
                [newClient] = self.accept_connections()
                self.__currentPlayers[newClient] = {'id': len(self.__currentPlayers),
                                                'status': Server.ClientStatus.CONNECTED,
                                                'uname' : None,
                                                'animating': True}
                self.tx_message(newClient, ("ip-info", get_ip()))
                self.tx_message(newClient, ('name-request',))
        
    def remove_client(self, client):
        """
        Disconnects the client and stops the game

        Parameters
        ----------
        client: socket.socket
            The socket of the player who disconnected
        """
        super().remove_client(client)
        self.__stop_game("player-left", self.__currentPlayers[client]["uname"])
    
    def __broadcast_gamestate(self, stateTag: str):
        """
        Sends the gamestate to all players

        Parameters
        ----------
        stateTag: str
            The type of state being sent
        """
        for client in self.__currentPlayers.keys():
            # Get the gamestate package for that specific client and send it
            pkg = self.__package_gamestate(client)
            self.tx_message(client, ('state', stateTag, pkg))

    def __package_gamestate(self, client):
        """
        Pulls out the elements from our gamestate that a specific client needs 
        to know and packages them into a ClientStatePackage object

        Parameters
        ----------
        client: socket.socket
            The specific player's socket for whom the package is created

        Returns
        -------
        ClientStatePackage for the given client
        """
        clientIdx = self.__currentPlayers[client]['id']
        playerLayout, myDeckSize, midPiles, opponentInfo = self.__state.get_player_info(clientIdx)

        otherPlayerIdx = [subdict['id'] for subdict in self.__currentPlayers.values() if subdict.get('id') != clientIdx][0] # There will only be one in a two player game
        oppLayout = opponentInfo[otherPlayerIdx]['layout']
        theirDeckSize = opponentInfo[otherPlayerIdx]['cardsLeft']
        return ClientStatePackage(playerLayout, oppLayout, midPiles, myDeckSize, theirDeckSize)
    
    #*********************************************************************#
    #        Internal functions for gracefully ending the game            #
    #*********************************************************************#

    def __terminate_game(self, winnerId):
            """
            Correctly parse the information that needs to be sent to stop_game

            Parameters
            ----------
            winnerId: int | None
                The id of the player that won or None if the game is a draw
            
            Returns
            -------
            None

            """
            if winnerId != None:
                winner = self.__client_from_id(winnerId)
                self.__stop_game("winner", data=winner)
            else: # Draw
                self.__stop_game("draw")
            
    def __stop_game(self, reason, data=None):
        """
        Ends the game 

        Parameters
        ----------
        reason: any
            Why the game is stopping
        data: any
            the data to include in the message
        """
        if self.__serverStatus != Server.ServerStatus.STOPPING:
            self.__serverStatus = Server.ServerStatus.STOPPING
            if reason == "winner":
                # in this case, data == client socket that won
                self.__broadcast_gamestate("new")
                self.exclusive_broadcast([data], ("game-stopped", "lost", self.__currentPlayers[data]['uname']))
                self.tx_message(data, ("game-stopped", "won", "CONGRATS!"))
            else:
                self.broadcast_message(('game-stopped', reason, data))  

    #*********************************************************************#
    #                Internal Functions for status checking               #
    #*********************************************************************#

    def __enough_joined(self):
        """
        Returns
        -------
        : bool
            True if at least maxPlayers have connected otherwise False
        """
        return len(self.__currentPlayers) >= self.__maxPlayers
    
    def __all_ready(self):
        """
        Returns
        -------
        : bool
            An indicator if enough players have the READY status
        """
        return all(map(lambda a : a["status"] == Server.ClientStatus.READY, self.__currentPlayers.values())) and self.__enough_joined()
    
    def __all_named(self):
        """
        Returns
        -------
        : bool
            An indicator if every player has a user name      
        """
        return all(map(lambda x: x['uname'] != None, self.__currentPlayers.values())) and self.__enough_joined()
    
    def __any_animating(self):
        """
        Check if any players are currently animating 

        Returns
        -------
        : bool
            True if any player is animating, else False
        
        """
        return any([v['animating'] for v in self.__currentPlayers.values()])
    
    #*********************************************************************#
    #                       Internal helper getters                       #
    #*********************************************************************#
    
    def __player_names(self):
        """
        Returns
        -------
        : list(str)
            A list of all connected players user names
        """
        return list(map(lambda x: x['uname'], self.__currentPlayers.values()))

    def __client_from_id(self, id):
        """
        Get the socket object of the winner from their id

        Parameters
        ----------
        id: int
            The id number of the player who won

        Returns
        -------
        client: socket.socket
            The socket of the player who won
        """
        for client, clientDict in self.__currentPlayers.items():
            if clientDict["id"] == id:
                return client

# SERVER_ADDR = "localhost"
SERVER_ADDR = "0.0.0.0"
SERVER_PORT = 9000

def main():
    server = Server(SERVER_ADDR, SERVER_PORT, 2)
    print(f"Created a server at {get_ip()}:{9000}")
    server.start()

if __name__ == "__main__":
    main()