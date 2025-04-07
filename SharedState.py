import threading

class PlayCardAction():
    def __init__(self, layoutIdx, midPileIdx):
        self.layoutIdx = layoutIdx
        self.midPileIdx = midPileIdx

# TODO -- Send this to its own file
class ClientStatePackage():
    """
    A package for communication about the game between the server and the client
    about the relevant game objects
    """     
    
    def __init__(self, myLayout, theirLayout, midPiles): 
        """
        Constructor for the ClientStatePackage object

        Parameters
        ----------
        myLayout : list(Card)
            The cards that this player has in their layout
        theirLayout : list(Card)
            The cards the other player has in their layout
        midPiles : list(Card)
            The cards on the center piles
        
        Returns
        -------
        A ClientStatePackage object
        """
        self.myLayout    = myLayout
        self.theirLayout = theirLayout
        self.midPiles    = midPiles
    
    def __str__(self):
        return f"ClientStatePackage: My Piles: {[str(c) for c in self.myLayout]},\nTheir Piles: {[str(c) for c in self.theirLayout]},\nMid Piles: {[str(c) for c in self.midPiles]}"


# This class wraps a client state package object and can be shared across 
# threads to give multiple threads a way to access/change client state
class ClientState():

    def __init__(self, gameState: ClientStatePackage):
        """
        A contructor for a ClientState object which is intended to be shared
        between a Client and a Display

        Parameters
        ----------
        gameState : ClientStatePackage
            The initial state for the client

        Returns
        -------
        A ClientState object
        """
        self.monitor = threading.Lock()
        self.__gameState = gameState
        self.__hasData = False if gameState is None else True

    def update_state(self, newState):
        """
        Change the reference to client state to a new object.

        Parameters:
        ----------
        newState : ClientStatePackage

        Effects:
        -------
        Cha
        """
        with self.monitor:
            self.__gameState = newState
            self.__hasData = False if newState is None else True

    def has_data(self):
        with self.monitor:
            return self.__hasData

    def get_state(self):
        """
        A getter for the current gamestate from the client's perspective

        Returns
        -------
        myLayout: list(Card)
            The layout of this player
        theirLayout: list(Card)
            The layout of the opponent player
        midPiles: list(Card)
            The cards in the center that players can play onto
        realCards: list(bool)
            Whether or not a specific layout pile in myLayout is nonempty
        """
        with self.monitor:
            if not self.__hasData:
                return None, None, None
            myLayout    = self.__gameState.myLayout.copy()
            theirLayout = self.__gameState.theirLayout.copy()
            midPiles = self.__gameState.midPiles.copy()

        return myLayout, theirLayout, midPiles, [c != None for c in myLayout]
        
    
    def __str__(self):
        return f"ClientState: {self.__gameState}"


