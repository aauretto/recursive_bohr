# File containing the definition for a card
from enum import Enum

class Card:
    """
    Card class
    Holds a rank and suit as well as some utility functions for creating cards
    and displaying cards.
    """

    """
    Suit class
    Class that simply enumerates the 4 card suits
    """
    class Suit(Enum):
        SPADES   = 0
        CLUBS    = 1
        HEARTS   = 2
        DIAMONDS = 3

    # Ranks for readability:
    __ranks = {
        "A" : 1,
        "2" : 2,
        "3" : 3,
        "4" : 4,
        "5" : 5,
        "6" : 6,
        "7" : 7,
        "8" : 8,
        "9" : 9,
        "10" :10,
        "J" : 11,
        "Q" : 12, 
        "K" : 13
    }
    __rankString = ["a", "2", "3", "4", "5", "6", "7", "8", "9", "10", "j", 
                    "q", "k"]
    __suitString = {Suit.SPADES   : "s", 
                    Suit.CLUBS    : "c", 
                    Suit.HEARTS   : "h", 
                    Suit.DIAMONDS : "d"}


    def __init__(self, rank: int, suit: Suit):
        """
        Constructor for the Card class.

        Parameters
        ----------
        rank: int
            the rank of the card (aces have rank 1)
        suit: Suit
            the Suit of the card 

        Returns
        -------
        Card
        """
        self.__rank = rank
        self.__suit = suit

    def suit(self):
        """
        Returns the Suit of a Card

        Returns
        -------
        : Suit
            the Suit of the Card this method is being called on
        """
        return self.__suit
    def rank(self):
        """
        Returns the rank of a Card

        Returns
        -------
        : int
            the rank of the Card this method is being called on
        """
        return self.__rank
    

    def __str__(self):
        """
        Converts a card to string with the format rank_[first letter of suit]
        where ranks for face cards are j, k, q, and a.

        Returns
        -------
        : int
            the rank of the Card this method is being called on
        """
        return self.__rankString[self.__rank - 1] + "_" + self.__suitString[self.__suit]
    
    @staticmethod
    def are_adjacent(card1, card2):
        """
        Checks if two cards differ in ranks by 1. Aces are treated
        as differing in ranks by 1 from both 2's and Kings.  

        Parameters
        ----------
        card1: Card
            The first Card to compare
        card2: Card
            The second Card to compare

        Returns
        -------
        : bool
            True if the cards are adjacent in rank, False otherwise      
        """

        if abs(card1.rank() - card2.rank()) == 1:
            return True
        # Accounting for aces being able to be played high/low
        elif abs(card1.rank() - card2.rank()) == 12:
            return True
        return False
