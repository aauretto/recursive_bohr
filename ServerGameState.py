"""
File: ServerGameState.py
Authors: Aiden Auretto, Peter Scully, Simon Webber, Claire Williams
Date: 4/28/2025

Purpose
------- 
    This file contains the Player class, which contains the data 
    about the player and operations to change its state. This file
    also contains the ServerGameState class, which contains the 
    state of the game from the server side and operations to 
    modify it. 
"""

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
        self.__deck = deck
        self.__name = name
        self.__id = id
        self.__layout = deck.deal(layoutSize)

    def get_layout(self):
        """
         Returns the player's full layout
 
         Returns
         -------
         : list(Card)
             A copy of the list of Cards in the Player's layout
         """
        return self.__layout.copy()

    def deal_card(self):
        """
         Removes and returns the top card of the Player's Deck
         
         Returns
         -------
         : Card
             The Card dealt from the Player's Deck
         """
        return self.__deck.deal(1)[0]

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
        return self.__layout[index]
    
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
        card = self.__layout[layoutIndex]
        try:
            self.__layout[layoutIndex] = self.__deck.deal(1)[0]
        except:
            self.__layout[layoutIndex] = None
        return card

    def cards_left(self):
        """
         Returns the number of cards left in the Player's Deck
         
         Returns
         -------
         : int
             The number of cards left in the Deck
         """
        return len(self.__deck)

    
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
        self.__players = []
        self.__layoutSize = layoutSize
        for i in range(numPlayers):
            new_deck = Deck()
            new_deck.shuffle()
            self.__players.append(Player(new_deck, i, layoutSize))

        # Create game piles from players' decks
        # For fairness, num_game_piles should be divisible by num_players
        self.__game_piles = []
        for i in range(numGamePiles):
            top_card = self.__players[i % numPlayers].deal_card()
            self.__game_piles.append(top_card)


    def __deal_game_pile(self):
        """
        Deals out a card from each player's deck to the game piles 

        Returns
        -------
        : list(int)
         The list of indices of the players that flipped
        """
        flippedPlayers = []

        for i in range(len(self.__players)):
            if not self.__players[i].cards_left() == 0:
                dealtCard = self.__players[i].deal_card()
                self.__game_piles[i] = dealtCard
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
        for player in self.__players:
            for i in range(self.__layoutSize):
                if player.get_card(i) is not None:

                    # Check to see if it can be played on each game pile
                    for middleCard in self.__game_piles:
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
        playerCard = self.__players[playerIndex].get_card(layoutIndex)
        return playerCard and Card.are_adjacent(playerCard, 
                                                self.__game_piles[centerIndex])
            
    def get_game_piles(self):
        return self.__game_piles.copy()
    
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
            card = self.__players[playerIndex].play_card(layoutIndex)
            self.__game_piles[centerIndex] = card
            return True
        else:
            return False

    def game_over(self):
        """
        Checks if the game is over
        
        Returns
        -------
        : tuple(bool, int|None)
            Tuple signifying whether the game is over and the index of the 
            player that won or none if no player won.
        """
        # no moves available AND all decks empty  => DRAW
        if not self.moves_available() and \
            all([p.cards_left() == 0 for p in self.__players]):
            counts = [sum(1 for card in player.get_layout() 
                          if card is not None) for player in self.__players]
            if len(set(counts)) == 1:
                return (True, None)
            else:
                return (True, counts.index(min(counts)))
        else:
            # OR one persons layout is empty AND their deck is empty => WINNER
            for idx, player in enumerate(self.__players): 
                if all(c is None for c in player.get_layout()) and \
                    player.cards_left() == 0:
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
        thisPlayer = self.__players[playerIdx]
        otherPlayerInfo = {}
        for i, player in enumerate(self.__players):
            if i != playerIdx:
                otherPlayerInfo[i] = {'layout'   : player.get_layout(),
                                    'cardsLeft': player.cards_left()}
        return thisPlayer.get_layout(), thisPlayer.cards_left(), \
               self.__game_piles.copy(), otherPlayerInfo