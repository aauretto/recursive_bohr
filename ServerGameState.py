import Card
import Deck
from math import abs

class Player:
    def __init__(self, deck, id, name="Simon Webber", layoutSize=4):
        """
        Constructor creates a Player from a given deck, id, and name
        The Player's deck is then dealt into a layout of size LayoutSize
        """
        self.deck = deck
        self.name = name
        self.id = id
        self._layout = deck.deal(layoutSize)

    def get_layout(self):
        return self._layout

    # def attemptPlay(index): DONT KNOW WHAT ATTEMPT PLAY DOES HERES GETCARD

    def get_card(self, index):
        return self._layout[index]
    
    def play_card(self, layoutIndex):
        card = self._layout[layoutIndex]
        self._layout[layoutIndex] = self.deck.deal(1)[0]
        return card

    
class ServerGameState:
    def __init__(self, numPlayers=2, numGamePiles=2, layoutSize=4):
        """
        Constructor creates a server game state with numPlayers players, 
        each of which have their own decks and layouts of size layoutSize.
        All numGamePiles game piles are then given a starting top card by
        dealing from each players' decks. To take the same number of cards
        from every players' deck, make sure to make numGamePiles divisible
        by numPlayers.
        """

        # Create players
        self.players = []
        self.layoutSize = layoutSize
        for i in range(numPlayers):
            new_deck = Deck()
            new_deck.shuffle()
            self.players.append(Player(new_deck, i, layoutSize))

        # Create game piles from players' decks
        # For fairness, num_game_piles should be divisible by num_players
        self.game_piles = []
        for i in range(numGamePiles):
            top_card = self.players[i % numPlayers].deck.deal(1)[0]
            self.game_piles.append(top_card)
        
        self.winner = None

    def __are_adjacent(card1, card2):
        """
        Returns true if two cards differ in ranks by 1. Aces are treated
        as differing in ranks by 1 from both 2's and Kings.        
        """

        if abs(card1.rank() - card2.rank()) == 1:
            return True
        # Accounting for aces being able to be played high/low
        elif abs(card1.rank() - card2.rank()) == 13:
            return True
        return False

    def __deal_game_pile(self):
        """
        Deals out a card from each player's deck to the game piles  
        """
        for i in range(len(self.players)):
            self.game_piles[i] = self.players[i].deck.deal(1)[0]

    def __validate_game_state(self):
        """
        Function to check whether a game state is valid. Keeps dealing a
        card from each players' decks to the game pile until a va
        """
        isValid = False
        for player in self.players:
            for i in range(self.layoutSize):
                for middle_card in self.game_piles:
                    if self.__are_adjacent(player.getCard(i), middle_card):
                        isValid = True
        if not isValid:
            self.__deal_game_pile()
            self.__validate_game_state()

    def __is_play_valid(self, playerIndex, layoutIndex, centerIndex):
        """
        Returns boolean indicating whether or not a play is valid
        """
        playerCard = self.players[playerIndex].getCard[layoutIndex]
        return self.__are_adjacent(playerCard, self.game_piles[centerIndex])
            

    # note: got rid of the tuple from the design doc 
    def play_card(self, playerIndex, layoutIndex, centerIndex):
        if (self.__is_play_valid(playerIndex, layoutIndex, centerIndex)):
            # NOT FINISHED ADD HERE 
            self.__validate_game_state


        