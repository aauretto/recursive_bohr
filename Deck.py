from Card import Card
import random

class EmptyDeckError(Exception):
    pass

class Deck():
    def __init__(self):
        """
         Constructor for the Deck class. Creates standard 52 Card deck
 
         Returns
         -------
         : Deck
         """
        self.__theDeck = []

        # create deck of 52 standard cards:
        # for s in (Card.Suit.SPADES, Card.Suit.HEARTS, Card.Suit.CLUBS, 
        #           Card.Suit.DIAMONDS):
        #     for r in range(1, 14):
        #         self.__theDeck.append(Card(r, s))
        self.__theDeck.append(Card(1, Card.Suit.SPADES))
        self.__theDeck.append(Card(2, Card.Suit.SPADES))
        self.__theDeck.append(Card(3, Card.Suit.SPADES))
        self.__theDeck.append(Card(4, Card.Suit.SPADES))
        self.__theDeck.append(Card(5, Card.Suit.SPADES))
    def shuffle(self):
        """
         Shuffles the order of the deck
 
         Returns
         -------
         None
         """
        random.shuffle(self.__theDeck)
        
    def __len__(self):
        """
         Gets size of deck
 
         Returns
         -------
         : int 
             the number of cards currently in the deck
         """
        return len(self.__theDeck)

    def deal(self, numToDeal):
        """
         Removes and returns the top numToDeal cards from the deck.
         Errors if you try to deal more cards than are in the deck.
         
         Parameters
         ----------
         numToDeal: int
             the number of cards to deal out
 
         Returns
         -------
         toRet: list(Card) 
             a list of cards of length numToDeal
         """
        if numToDeal > self.__len__():
            raise EmptyDeckError("Deck is empty")
        
        toRet = self.__theDeck[0:numToDeal]
        self.__theDeck = self.__theDeck[numToDeal:]
        return toRet
    
    def is_empty(self):
        """
        Returns
        -------
        True if there are no cards in the deck else False
        """
        return len(self) == 0