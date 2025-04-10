from Card import *
import random

class EmptyDeckError(Exception):
    pass

class Deck():
    def __init__(self):
        self.theDeck = []

        # create deck of 52 standard cards:
        for s in (Card.Suit.SPADES, Card.Suit.HEARTS, Card.Suit.CLUBS, Card.Suit.DIAMONDS):
            for r in range(1, 14):
                self.theDeck.append(Card(r, s))

    def shuffle(self):
        random.shuffle(self.theDeck)
        
    def __len__(self):
        return len(self.theDeck)

    def deal(self, numToDeal):
        try: 
            toRet = self.theDeck[0:numToDeal]
        except:
            raise EmptyDeckError("Deck is empty")
        self.theDeck = self.theDeck[numToDeal:]
        return toRet
    
    def is_empty(self):
        return len(self) == 0

    def reset(self):
        self.__init__()