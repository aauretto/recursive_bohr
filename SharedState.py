"""
File: SharedState.py
Authors: Aiden Auretto, Peter Scully, Simon Webber, Claire Williams
Date: 4/28/2025

Purpose
------- 
    This file is a wrapper to cleanly export a number of classes that
    are shared between other different classes throughout the program.
"""
import threading

class PlayCardAction():
    def __init__(self, layoutIdx, midPileIdx):
        """
        Constructor

        Parameters
        ----------
        layoutIdx: int
            The index of the card being played
        midPileIdx: int
            The index of the card being played onto
        """
        self.layoutIdx = layoutIdx
        self.midPileIdx = midPileIdx

class ClientStatePackage():
    """
    A package for communication about the game between the server and the client
    about the relevant game objects
    """     
    
    def __init__(self, myLayout, theirLayout, midPiles, myDeckSize, 
                 theirDeckSize): 
        """
        Constructor for the ClientStatePackage object

        Parameters
        ----------
        myLayout: list(Card)
            The cards that this player has in their layout
        theirLayout: list(Card)
            The cards the other player has in their layout
        midPiles: list(Card)
            The cards on the center piles
        myDeckSize: int 
            The number of cards left in this player's deck
        theirDeckSize: int
            The number of cards left in the opponent's deck
        
        Returns
        -------
        : ClientStatePackage
        """
        self.myLayout    = myLayout
        self.theirLayout = theirLayout
        self.midPiles    = midPiles
        self.myDeckSize = myDeckSize
        self.theirDeckSize = theirDeckSize
    

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
        : ClientState
        """
        self.__monitor = threading.Lock()
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
        Overwrites the current state entirely
        """
        with self.__monitor:
            self.__gameState = newState
            self.__hasData = False if newState is None else True

    def has_data(self):
        """
        Returns
        -------
        : bool
            True if the ClientState has data otherwise False
        """
        with self.__monitor:
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
        myDeckSize: int
            The number of cards left in my deck
        theirDeckSize: int
            The number of cards left in their deck
        """
        with self.__monitor:
            if not self.__hasData:
                return [None], [None], [None], [False], 0, 0
            myLayout    = self.__gameState.myLayout.copy()
            theirLayout = self.__gameState.theirLayout.copy()
            midPiles = self.__gameState.midPiles.copy()
            myDeckSize = self.__gameState.myDeckSize
            theirDeckSize = self.__gameState.theirDeckSize

        return myLayout, theirLayout, midPiles, \
               [c != None for c in myLayout], myDeckSize, theirDeckSize
        

    def shape(self):
        """
        Returns the number of piles for us, our opponent, and in the middle

        Returns
        -------
        :tuple(int, int, int)
            Where the first element is the number of our piles
            The second element is the number of their piles
            The final element is the number of middle piles
        """
        myLayout, theirLayout, midPiles, _, _, _ = self.get_state()
        return (len(myLayout), len(theirLayout), len(midPiles))    
        