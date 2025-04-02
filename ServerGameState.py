from Card import Card
from Deck import Deck

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
    def deal_card(self):
        return self.deck.deal(1)[0]

    def get_card(self, index):
        return self._layout[index]
    
    def play_card(self, layoutIndex):
        card = self._layout[layoutIndex]
        try:
            self._layout[layoutIndex] = self.deck.deal(1)[0]
        except Deck.EmptyDeckError:
            self._layout[layoutIndex] = None
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
            top_card = self.players[i % numPlayers].deal_card()
            self.game_piles.append(top_card)
        
        self._winner = None
        self._gameOver = False

    def __deal_game_pile(self):
        """
        Deals out a card from each player's deck to the game piles 

        Declares a draw if everyone's decks are empty 
        """
        emptyDecks = 0
        for i in range(len(self.players)):
            try:
                self.game_piles[i] = self.players[i].deck.deal(1)[0]
            except Deck.EmptyDeckError:
                emptyDecks += 1

        if emptyDecks == len(self.players):
            self._gameOver = True


    def __validate_game_state(self):
        """
        Function to check whether a game state is valid. Keeps dealing a
        card from each players' decks to the game pile until a valid gamestate
        is reached

        Declares a draw if each players' decks are empty and nobody can make a
        move
        """
        isValid = False
        for player in self.players:
            for i in range(self.layoutSize):
                for middleCard in self.game_piles:
                    if Card.are_adjacent(player.get_card(i), middleCard):
                        isValid = True
        if not isValid:
            print("deadlock!!!")
            self.__deal_game_pile()
            self.__validate_game_state()

    def __is_play_valid(self, playerIndex, layoutIndex, centerIndex):
        """
        Returns boolean indicating whether or not a play is valid
        """
        playerCard = self.players[playerIndex].get_card(layoutIndex)
        return playerCard and Card.are_adjacent(playerCard, 
                                                  self.game_piles[centerIndex])
            

    # note: got rid of the tuple from the design doc 
    def play_card(self, playerIndex, layoutIndex, centerIndex):
        if (self.__is_play_valid(playerIndex, layoutIndex, centerIndex)):
            card = self.players[playerIndex].play_card(layoutIndex)
            self.game_piles[centerIndex] = card
            if all(c is None for c in self.players[playerIndex].get_layout()):
                self._winner = self.players[playerIndex]
                self._gameOver = True
                return True
            self.__validate_game_state()
            return True
        else:
            return False

    def game_over(self):
        return self._gameOver

    def get_winner(self):
        return self._winner        