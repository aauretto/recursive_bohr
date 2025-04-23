from Card import Card
from Deck import Deck

class Player:
    def __init__(self, deck, id, name=None, layoutSize=4):
        """
         Constructor for a Player
         Deals out the player's initial layout         
         
         Parameters
         ----------
         deck: Deck
             Deck for the player to start with
         id: int
             Integer id for the player
         name: str
            The name of this player
         layoutSize: int
             Number of cards to deal out from Deck into the player's layout
         
         Returns
         -------
         Player
         """
        self.deck = deck
        self.name = name
        self.id = id
        self._layout = deck.deal(layoutSize)

    def get_layout(self):
        """
         Returns the player's full layout
 
         Returns
         -------
         : list(Card)
             A copy of the list of Cards in the Player's layout
         """
        return self._layout.copy()

    def deal_card(self):
        """
         Removes and returns the top card of the Player's Deck
         
         Returns
         -------
         : Card
             The Card dealt from the Player's Deck
         """
        return self.deck.deal(1)[0]

    def get_card(self, index):
        """
         Gets the card at a given index the Player's layout
 
         Parameters
         ----------
         index: int
             Index of the desired card in the Player's layout
         
         Returns
         -------
         : Card
             The Card at that index in the Player's layout
         """
        return self._layout[index]
    
    def play_card(self, layoutIndex):
        """
         Takes the card off of the given index from the Player's layout and
         replaces it with the next Card on the Player's Deck (or None if the
         Deck is empty)
 
         Parameters
         ----------
         layoutIndex: int
             The index of the layout that the Card to remove is stored at
         
         Returns
         -------
         : Card
             The Card removed from the Player's layout
         """
        card = self._layout[layoutIndex]
        try:
            self._layout[layoutIndex] = self.deck.deal(1)[0]
        except:
            self._layout[layoutIndex] = None
        return card

    def cards_left(self):
        """
         Returns the number of cards left in the Player's Deck
         
         Returns
         -------
         : int
             The number of cards left in the Deck
         """
        return len(self.deck)

    
class ServerGameState:
    def __init__(self, numPlayers=2, numGamePiles=2, layoutSize=4):
        """
        Constructor for the ServerGameState
        Deals out player's layouts and then deals a card from each to a 
        center pile

        Parameters
        ----------
        numPlayers: int
            The number of players playing the game. Default is 2
        numGamePiles: int
            The number of center piles in the game. Defualt is 2
        layoutSize: int
            The number of cards in each player's layout. Default is 4

        Returns
        -------
        : ServerGameState
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


    def __deal_game_pile(self):
        """
        Deals out a card from each player's deck to the game piles 

        Returns
        -------
        : list(int)
         The list of indices of the players that flipped
        """
        flippedPlayers = []

        for i in range(len(self.players)):
            if not self.players[i].deck.is_empty():
                dealtArray = self.players[i].deck.deal(1)
                self.game_piles[i] = dealtArray[0]
                flippedPlayers.append(i)
        return flippedPlayers
    
    def moves_available(self):
        """
        Checks if there are valid moves that can be played

        Returns
        -------
        : bool
            True if moves are available else False
        
        """
        # For each card in each players layout that is a real card
        for player in self.players:
            for i in range(self.layoutSize):
                if player.get_card(i) is not None:

                    # Check to see if it can be played on each game pile
                    for middleCard in self.game_piles:
                        if Card.are_adjacent(player.get_card(i), middleCard):
                            return True 
        return False

    def flip(self):
        """
        Flips a card from each player (if possible) from their deck to their
        corresponding mid pile

        Returns
        -------
        : list(int)
            The list of indices of the players that flipped
        """
        (gameOver, _) = self.game_over()
        # Only flip at the correct time
        if not self.moves_available() and not gameOver:
            return self.__deal_game_pile()
        return []

    def __is_play_valid(self, playerIndex, layoutIndex, centerIndex):
        """
        Verifies that a given play is valid

        Parameters
        ----------
        playerIndex: int
            The index of the player attempting the move
        layoutIndex: int
            The index of the card in the player's layout that they are 
            attempting to play
        centerIndex: int
            The index of the mid pile the player is attempting to play onto
        
        Returns
        -------
        : bool
            Indicator of whether or not a play is valid
        """
        if self.game_over()[0]:
            return False
        playerCard = self.players[playerIndex].get_card(layoutIndex)
        return playerCard and Card.are_adjacent(playerCard, 
                                                  self.game_piles[centerIndex])
            

    def play_card(self, playerIndex, layoutIndex, centerIndex):
        """
        Plays a card

        Parameters
        ----------
        playerIndex: int
            The index of the player attempting the move
        layoutIndex: int
            The index of the card in the player's layout that they are 
            attempting to play
        centerIndex: int
            The index of the mid pile the player is attempting to play onto
        
        Returns
        -------
        : bool
            Indicator of whether or not a play is valid / happened
        """
        if (self.__is_play_valid(playerIndex, layoutIndex, centerIndex)):
            card = self.players[playerIndex].play_card(layoutIndex)
            self.game_piles[centerIndex] = card
            return True
        else:
            return False

    def game_over(self):
        """
        Checks if the game is over
        
        Returns
        -------
        : tuple(bool, int|None)
            Tuple signifying whether the game is over and the index of the player
            that won or none if no player won.
        """
        # no moves available AND all decks empty  => DRAW
        if not self.moves_available() and all([p.deck.is_empty() for p in self.players]):
            counts = [sum(1 for card in player.get_layout() if card is not None) for player in self.players]
            if len(set(counts)) == 1:
                return (True, None)
            else:
                return (True, counts.index(min(counts)))
        else:
            # OR one persons layout is empty AND their deck is empty => WINNER
            for idx, player in enumerate(self.players): 
                if all(c is None for c in player.get_layout()) and player.deck.is_empty():
                    return (True, idx)
            # Game is not over
            return (False, None)
            
    def get_player_info(self, playerIdx):
        """
        Gets the gamestate for a single player

        Parameters
        ----------
        playerIdx: int
            The index of the player to fetch information for
        
        Returns
        -------
        : tuple(list(Card), list(Card), list(Card), int, int)
        """
        thisPlayer = self.players[playerIdx]
        otherPlayerInfo = {}
        for i, player in enumerate(self.players):
            if i != playerIdx:
                otherPlayerInfo[i] = {'layout'   : player.get_layout(),
                                    'cardsLeft': player.cards_left()}
        return thisPlayer.get_layout(), thisPlayer.cards_left(), self.game_piles.copy(), otherPlayerInfo