from IPCutils import *
from ServerGameState import *
from enum import Enum
from functools import *
from SharedState import ClientStatePackage, PlayCardAction

import time

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

        
    def start(self):
        while len(self.currentPlayers) < self.maxPlayers:
            self.handle_connection()

        self.broadcast_message(('name-request',))
        while not self.__all_named():
            self.rx_message()

        # Tell everyone that everyone connected
        player_names = self.__player_names()
        self.broadcast_message(("everybody-joined", player_names))

        while not self.__all_ready():
            self.rx_message()

        self.serverStatus = ServerStatus.RUNNING

        self.broadcast_gamestate('initial')
        self.__loop()

    def __player_names(self):
        return list(map(lambda x: x['uname'], self.currentPlayers.values()))
    
    def __all_ready(self):
        return all(map(lambda a : a["status"] == ClientStatus.READY, self.currentPlayers.values()))
    

    def __loop(self):
        ### DO LOOP THINGS
        while self.serverStatus == ServerStatus.RUNNING:
            self.rx_message()

    def __all_named(self):
        return all(map(lambda x: x['uname'] != None, self.currentPlayers.values()))

    # Override handle_message
    def handle_message(self, client, msg):
        print(f"Server received {msg}")
        if self.serverStatus == ServerStatus.SETUP:
            ### Wait unitl all clients say they are ready

            match msg:
                case ("player-name", name):
                    self.currentPlayers[client]["uname"] = name
                case ("ready",):
                    self.currentPlayers[client]['status'] = ClientStatus.READY
                case _:
                    print(f"Non-ready msg received: {msg}")
        elif self.serverStatus == ServerStatus.RUNNING:
            ### Handle moves and game logic
            match msg:
                case ("play", playAction):    
                    self.handle_play(client, playAction)
                case ("quitting",):
                    self.__stop_game("player-left", self.currentPlayers[client]['uname'])

    def __winner_from_id(self, id):
        for client, clientDict in self.currentPlayers:
            if clientDict["id"] == id:
                return client

    def exclusive_broadcast(self, clientsToExclude, msg):
        """
        Broadcasts a message to all but clients in list clientsToExclude
        """
        for c in self.clients:
            if c not in clientsToExclude:
                self.tx_message(c, msg)

    def handle_play(self, client, playAction):
        clientIdx = self.currentPlayers[client]["id"]
        validMove = self.state.play_card(clientIdx, 
                                            playAction.layoutIdx, 
                                            playAction.midPileIdx)
        if validMove:
            self.broadcast_gamestate("new")
        else:
            self.tx_message(client, 
                            ("bad-move", 
                            self.__package_gamestate(client)))

        if self.state.game_over():
            if winnerId := self.state.get_winner():
                winner = self.__winner_from_id(winnerId)
                self.__stop_game("winner", data=winner)
            else: # Draw
                self.__stop_game("draw")
            

    def handle_connection(self):
        if len(self.currentPlayers) >= self.maxPlayers:
            self.reject_connections()
        else:
            [newClient] = self.accept_connections()
            self.currentPlayers[newClient] = {'id': len(self.currentPlayers),
                                              'status': ClientStatus.CONNECTED,
                                              'uname' : None}
            #TODO send clients a waiting for everyone to join message
            #if we dont get enough conx in time t, then disconnect everyone
    
    def broadcast_gamestate(self, stateTag: str):
        for client in self.currentPlayers.keys():
            pkg = self.__package_gamestate(client)
            self.tx_message(client, ('state', stateTag, pkg))
            
    
    def __package_gamestate(self, client):
        """
        Pulls out the elements from our gamestate that a specific client needs 
        to know and packages them into a ClientStatePackage object
        """
        clientIdx = self.currentPlayers[client]['id']
        playerLayout, oppLayout, midPiles, myDeckSize, theirDeckSize = self.state.get_player_info(clientIdx)
        return ClientStatePackage(playerLayout, oppLayout, midPiles, myDeckSize, theirDeckSize)

    def remove_client(self, client):
        super().remove_client(client)
        self.__stop_game("player-left", self.currentPlayers[client]["uname"])
        
    def __stop_game(self, reason, data=None):
        if self.serverStatus != ServerStatus.STOPPED:
            self.serverStatus = ServerStatus.STOPPED
            if reason == "winner":
                # in this case, data == client socket that won
                self.exclusive_broadcast([data], ("game-stopped", "lost", self.currentPlayers[data]['uname']))
                self.tx_message(data, ("game-stopped", "won", "CONGRATS!"))
            else:
                self.broadcast_message(('game-stopped', reason, data))  

# SERVER_ADDR = "localhost"
SERVER_ADDR = "0.0.0.0"
SERVER_PORT = 9000

def main():
    server = Server(SERVER_ADDR, SERVER_PORT, 2)
    print(f"Created a server on port {9000}")
    server.start()

if __name__ == "__main__":
    main()