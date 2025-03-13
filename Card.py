# File containing the definition for a card
from enum import Enum

class Card:
    """
    Card class
    Holds a rank and suit as well as some utility functions for creating cards
    and displaying cards.
    """
    class Suit(Enum):
        SPADES   = 0
        CLUBS    = 1
        HEARTS   = 2
        DIAMONDS = 3

    # Suits for readability:
    __suits = {
        "S" : Suit.SPADES, 
        "C" : Suit.CLUBS, 
        "H" : Suit.HEARTS,
        "D" : Suit.DIAMONDS
    }
    __suitString = ["♠", "♣", "♥", "♦"]

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
    __rankString = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    def __init__(self, rank: int, suit: Suit):
        self.__rank = rank
        self.__suit = suit
    
    def read_card(self, s):
        try:
            # Extract rank and suit from input
            if (s != ""):
                suitPart = self.__suits[s[-1].upper()]
                rankPart = self.__ranks[s[0:-1].upper()]
                self.__rank = rankPart
                self.__suit = suitPart
        except:
            raise Exception("read_card unable to parse Input: \"" + s + "\"."
                            "Expected format: <Rank><Suit>")

    def suit(self):
        return self.__suit
    def rank(self):
        return self.__rank
    

    def __str__(self):
        return self.__rankString[self.rank] + " " + self.__suitString[self.suit.value]


