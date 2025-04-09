from IPCutils import *
from ServerGameState import *
from enum import Enum
from functools import *
from SharedState import ClientStatePackage, PlayCardAction
import socket

class ClientStatus(Enum):
    CONNECTED = 0
    READY     = 1
    PLAYING   = 2 

class ServerStatus(Enum):
    SETUP   = 0
    RUNNING = 1
    STOPPED = 2

class Server(BaseServer):
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
        self.currentPlayers = {}
        self.maxPlayers = numPlayers
        self.serverStatus = ServerStatus.SETUP

        self.state = ServerGameState(numPlayers=numPlayers, 
                                     numGamePiles=numGamePiles, 
                                     layoutSize=layoutSize)
        self.playerIsAnimating = [False] * numPlayers
        
    def start(self):
        """
        Starts up the server and run the game
        """

        # Wait for enough players to be connected
        while len(self.currentPlayers) < self.maxPlayers:
            self.handle_connection()

        # Request everyone's name and make sure everyone has a name
        self.broadcast_message(('name-request',))
        while not self.__all_named():
            self.rx_message()

        while not self.__all_ready():
            self.rx_message()

        self.serverStatus = ServerStatus.RUNNING
        self.broadcast_message(("everybody-joined", self.__player_names()))

        # Give everyone the initial gamestate
        self.broadcast_gamestate('initial')
        self.__flip_if_able()

        # Beign the game
        self.__loop()

    def __player_names(self):
        """
        Returns
        -------
        list(str)
            A list of all connected players user names
        """
        return list(map(lambda x: x['uname'], self.currentPlayers.values()))
    
    def __all_ready(self):
        """
        Returns
        -------
        bool
            An indicator if every player has the READY status
        """
        return all(map(lambda a : a["status"] == ClientStatus.READY, self.currentPlayers.values()))
    
    def __all_named(self):
        """
        Returns
        -------
        bool
            An indicator if every player has a user name      
        """
        return all(map(lambda x: x['uname'] != None, self.currentPlayers.values()))

    def __loop(self):
        """
        Runs the game
        """
        ### TODO SOCKET TIMEOUT THINS
        
        while self.serverStatus == ServerStatus.RUNNING:
            self.rx_message()
    
    def __terminate_game(self):
        if winnerId := self.state.get_winner():
            winner = self.__winner_from_id(winnerId)
            self.__stop_game("winner", data=winner)
        else: # Draw
            self.__stop_game("draw")
    
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
        print(msg)
        if self.serverStatus == ServerStatus.SETUP:
            # We only want to handle these types of messages in the SETUP phase
            match msg:
                case ("player-name", name):
                    self.currentPlayers[client]["uname"] = name
                case ("ready",):
                    self.currentPlayers[client]['status'] = ClientStatus.READY
                case _:
                    print(f"Non-ready msg received: {msg}")
        elif self.serverStatus == ServerStatus.RUNNING:
            # Handle these messages while the game is running
            match msg:
                case ("play", playAction):    
                    self.handle_play(client, playAction)
                case ("quitting",):
                    self.__stop_game("player-left", self.currentPlayers[client]['uname'])
                case ("no-animations",):
                    clientIdx = self.currentPlayers[client]["id"]
                    self.playerIsAnimating[clientIdx] = False
                    if not self.__flip_if_able() and self.state.game_over(): 
                        self.__terminate_game()

    def __flip_if_able(self):
        if not any(self.playerIsAnimating) and not self.state.moves_available(): 
            if not self.state.game_over():
                oldPiles = self.state.game_piles
                self.state.flip()
                
                newPiles = self.state.game_piles
                self.broadcast_message(("flip", oldPiles, newPiles))
                self.broadcast_gamestate("new-state")
                return True
        return False

    def __winner_from_id(self, id):
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
        for client, clientDict in self.currentPlayers.items():
            if clientDict["id"] == id:
                return client

    def handle_play(self, client, playAction):
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
        clientIdx = self.currentPlayers[client]["id"]
        validMove = self.state.play_card(clientIdx, 
                                            playAction.layoutIdx, 
                                            playAction.midPileIdx)
        
        # If the move is allowed we send the new gamestate back to everyone
        if validMove:
            self.exclusive_broadcast([client], ("move", "them", playAction.layoutIdx, "mid", playAction.midPileIdx))
            self.tx_message(client, ("move", "me", playAction.layoutIdx, "mid", playAction.midPileIdx))
            self.broadcast_gamestate("new-state")
            self.playerIsAnimating[clientIdx] = True
        else:
            # Otherwise we tell the client they made a bad move
            self.tx_message(client, 
                            ("bad-move", 
                            self.__package_gamestate(client)))

        # If the game is done (someone won or a draw) we handle that
        if self.state.game_over():
            self.__terminate_game()

    def handle_connection(self):
        """
        Handles a new connection to the server
        """
        # If the game is full, reject new connections
        if len(self.currentPlayers) >= self.maxPlayers:
            self.reject_connections()
        else:
            # Otherwise accept the new connections and initialize them
            [newClient] = self.accept_connections()
            self.currentPlayers[newClient] = {'id': len(self.currentPlayers),
                                              'status': ClientStatus.CONNECTED,
                                              'uname' : None}
            self.tx_message(newClient, ("ip-info", get_ip()))
    
    def broadcast_gamestate(self, stateTag: str):
        """
        Sends the gamestate to all players

        Parameters
        ----------
        tag: str
            The type of state being sent
        """
        for client in self.currentPlayers.keys():
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
        clientIdx = self.currentPlayers[client]['id']
        playerLayout, oppLayout, midPiles, myDeckSize, theirDeckSize = self.state.get_player_info(clientIdx)
        return ClientStatePackage(playerLayout, oppLayout, midPiles, myDeckSize, theirDeckSize)

    def remove_client(self, client):
        """
        Disconnects the client and stops the game

        Parameters
        ----------
        client: socket.socket
            The socket of the player who disconnected
        """
        super().remove_client(client)
        self.__stop_game("player-left", self.currentPlayers[client]["uname"])
        
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
        if self.serverStatus != ServerStatus.STOPPED:
            self.serverStatus = ServerStatus.STOPPED
            if reason == "winner":
                # in this case, data == client socket that won
                self.broadcast_gamestate("new-state")
                self.exclusive_broadcast([data], ("game-stopped", "lost", self.currentPlayers[data]['uname']))
                self.tx_message(data, ("game-stopped", "won", "CONGRATS!"))
            else:
                self.broadcast_message(('game-stopped', reason, data))  

# SERVER_ADDR = "localhost"
SERVER_ADDR = "0.0.0.0"
SERVER_PORT = 9000

def main():
    server = Server(SERVER_ADDR, SERVER_PORT, 2)
    print(f"Created a server at {get_ip()}:{9000}")
    server.start()

if __name__ == "__main__":
    main()