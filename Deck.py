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
        self.theDeck = []

        # create deck of 52 standard cards:
        for s in (Card.Suit.SPADES, Card.Suit.HEARTS, Card.Suit.CLUBS, Card.Suit.DIAMONDS):
            for r in range(1, 14):
                self.theDeck.append(Card(r, s))
                
    def shuffle(self):
        """
         Shuffles the order of the deck
 
         Returns
         -------
         None
         """
        random.shuffle(self.theDeck)
        
    def __len__(self):
        """
         Gets size of deck
 
         Returns
         -------
         : int 
             the number of cards currently in the deck
         """
        return len(self.theDeck)

    def deal(self, numToDeal):
        """
         Removes and returns the top numToDeal cards from the deck
         
         Parameters
         ----------
         numToDeal: int
             the number of cards to deal out
 
         Returns
         -------
         toRet: list(Card) 
             a list of cards of length numToDeal
         """
        # TODO this will never except, how do we want to handle this
        try: 
            toRet = self.theDeck[0:numToDeal]
        except:
            raise EmptyDeckError("Deck is empty")
        self.theDeck = self.theDeck[numToDeal:]
        return toRet
    
    def is_empty(self):
        """
        Returns
        -------
        True if there are no cards in the deck else False
        """
        return len(self) == 0