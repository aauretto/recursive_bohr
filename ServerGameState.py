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
        deck.deal(40)
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
        except:
            self._layout[layoutIndex] = None
        return card

    def cards_left(self):
        return len(self.deck)

    
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
        
        self._winner = None
        self._gameOver = False

        # Create players
        self.players = []
        self.layoutSize = layoutSize
        for i in range(numPlayers):
            new_deck = Deck()
            new_deck.shuffle()
            # new_deck.deal(40) # TODO: Delete once done debugging
            self.players.append(Player(new_deck, i, layoutSize))

        # Create game piles from players' decks
        # For fairness, num_game_piles should be divisible by num_players
        self.game_piles = []
        for i in range(numGamePiles):
            top_card = self.players[i % numPlayers].deal_card()
            self.game_piles.append(top_card)

        # # Make sure someone can play
        # self.__validate_game_state()

    def __deal_game_pile(self):
        """
        Deals out a card from each player's deck to the game piles 

        Declares a draw if everyone's decks are empty 
        """
        emptyDecks = 0
        for i in range(len(self.players)):
            try:
                dealtArray = self.players[i].deck.deal(1)
                self.game_piles[i] = dealtArray[0]
            except:
                emptyDecks += 1

        if emptyDecks == len(self.players):
            self._gameOver = True


    def moves_available(self):
        for player in self.players:
            for i in range(self.layoutSize):
                if player.get_card(i) is not None:
                    for middleCard in self.game_piles:
                        if Card.are_adjacent(player.get_card(i), middleCard):
                            return True 
        return False

    ### TODO AIDEN FIX THIS
    def flip(self):
        self.__validate_game_state()

    def __validate_game_state(self):
        """
        Function to check whether a game state is valid. Keeps dealing a
        card from each players' decks to the game pile until a valid gamestate
        is reached

        Declares a draw if each players' decks are empty and nobody can make a
        move
        """
        if not self.moves_available() and not self.game_over():
            # If all players can flip, flip a card, otherwise we need to wait to
            # flip a card until players are ready to do so
            self.__deal_game_pile()
            # print("recursing on validate gamestate")
            # self.__validate_game_state()

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
                self._winner = playerIndex
                self._gameOver = True
                return True
            # self.__validate_game_state()
            return True
        else:
            return False

    def game_over(self):
        return self._gameOver

    def get_winner(self):
        return self._winner    
      
    def get_player_info(self, playerIdx):
        player = self.players[playerIdx]
        return player.get_layout().copy(), self.players[playerIdx - 1].get_layout().copy(), self.game_piles.copy(), player.cards_left(), self.players[playerIdx - 1].cards_left()