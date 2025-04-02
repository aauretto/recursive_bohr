from ServerGameState import ServerGameState 

def print_game_state(gameState):
    print(f"Game Piles: {[str(card) for card in gameState.game_piles]}")
    for player in gameState.players:
        print(f"Player: {[str(card) for card in player.get_layout()]}")

gameState = ServerGameState()
while not gameState.game_over():
    print_game_state(gameState)
    response = input("PlayerIndex, LayoutIndex, GamePileIndex")
    playerIndex = int(response[0])
    layoutIndex = int(response[1])
    gamePileIndex = int(response[2])
    gameState.play_card(playerIndex, layoutIndex, gamePileIndex)
print(gameState.get_winner())