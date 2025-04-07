import pygame
import sys
import math

# Initialize Pygame
# pygame.init()

# Set up the screen
# WIDTH = 1000
# HEIGHT = 800
# BACKGROUND_COLOR = (30, 92, 58)
# CARD_DIR = './card_pngs/'
# TARGET_WIDTH = 100 # px
# screen = pygame.display.set_mode((WIDTH, HEIGHT))
# pygame.display.set_caption("Draggable Playing Card")

# Load the playing card image (replace with your image path)
# my_cards = ['2_c', '3_h', '4_d', 'k_c']
# my_cards = [pygame.image.load(CARD_DIR + card + '.png') for card in my_cards]
# my_cards = [pygame.transform.scale(card, (card.get_width() // math.ceil(card.get_width() / TARGET_WIDTH), card.get_height() // math.ceil(card.get_width() / TARGET_WIDTH))) for card in my_cards]
# my_cards = [(card, card.get_rect()) for card in my_cards]

# mid_decks = ['6_c', 'q_h']
# mid_decks = [pygame.image.load(CARD_DIR + card + '.png') for card in mid_decks]
# mid_decks = [pygame.transform.scale(card, (card.get_width() // math.ceil(card.get_width() / TARGET_WIDTH), card.get_height() // math.ceil(card.get_width() / TARGET_WIDTH))) for card in mid_decks]
# mid_decks = [(card, card.get_rect()) for card in mid_decks]

# their_cards = ['j_s', '10_d', '7_h', '6_h']
# their_cards = [pygame.image.load(CARD_DIR + card + '.png') for card in their_cards]
# their_cards = [pygame.transform.scale(card, (card.get_width() // math.ceil(card.get_width() / TARGET_WIDTH), card.get_height() // math.ceil(card.get_width() / TARGET_WIDTH))) for card in their_cards]
# their_cards = [(card, card.get_rect()) for card in their_cards]

# Constants
# NUM_MY_PILES = 4
# NUM_THEIR_PILES = 4
# NUM_CENTER_PILES = 2

# screen.fill(BACKGROUND_COLOR)  # Fill screen with poker green

# # Do this every frame 
# theirPile_xlocs = [i * (WIDTH / (NUM_MY_PILES + 1)) for i in range(1, NUM_THEIR_PILES + 1)]
# theirPile_ylocs = [HEIGHT - (5 * (HEIGHT // (5 + 1)))] * NUM_THEIR_PILES
# for i, (card, card_rect) in enumerate(their_cards):
#     card_rect.center = (theirPile_xlocs[i], theirPile_ylocs[i])
#     screen.blit(card, card_rect)

# mid_piles_xlocs = [i * (WIDTH / (NUM_CENTER_PILES + 1)) for i in range(1, NUM_CENTER_PILES + 1)]
# mid_piles_ylocs = [HEIGHT - (3 * (HEIGHT // (5 + 1)))] * NUM_CENTER_PILES
# for i, (card, card_rect) in enumerate(mid_decks):
#     card_rect.center = (mid_piles_xlocs[i], mid_piles_ylocs[i])
#     screen.blit(card, card_rect)

# myPile_xlocs = [i * (WIDTH / (NUM_MY_PILES + 1)) for i in range(1, NUM_MY_PILES + 1)]
# myPile_ylocs = [HEIGHT - (HEIGHT // (5 + 1))] * NUM_MY_PILES
# for i, (card, card_rect) in enumerate(my_cards):
#     card_rect.center = (myPile_xlocs[i], myPile_ylocs[i])
#     screen.blit(card, card_rect)

##### HIGHLIGHT TESTING ######

# HIGHLIGHT_COLOR = (180, 0, 180, 100) # The color of the highlights that indicate which card is selected
# HIGHLIGHT_COLOR = (255, 0, 0, 100) # The color of the highlights that indicate which card is selected


# def make_border(rect_add, cntr_offset, rect, color, width = 5):
#     """
#     Creates a border

#     Parameters
#     ----------
#     rect_add : int
#         The amount around the rect to border
#     cntr_offset : int
#         The offset of the border center to the rect center
#     color : (int, int, int)
#         An RGB tuple for the color of the rectangle
#     width : int
#         The border width
#     """
#     surf = pygame.Surface((rect.w + rect_add, rect.h + rect_add), pygame.SRCALPHA)
#     hl_rect = pygame.draw.rect(surf, color, (0, 0, rect.width + rect_add, rect.height + rect_add), width = width)  # Transparent center
#     hl_rect.center = (rect.center[0] + cntr_offset, rect.center[1] + cntr_offset)
#     return surf, hl_rect

# def remove_border(border_idx):
#     (_, rect) = highlights[border_idx]
#     surf, rect = make_border(0, 0, rect, BACKGROUND_COLOR)
#     return surf, rect
# def remove_border_from(screen, border_idx):
#     surf, rect = remove_border(border_idx)
#     screen.blit(surf, rect)

# highlights = []
# for (card, rect) in my_cards:
#     hl_surf, hl_rect = make_border(10, .5, rect, HIGHLIGHT_COLOR)
#     highlights.append((hl_surf, hl_rect))

# Main game loop
# selected = False
# selected_idx= None
# while True:

#     if selected:
#         (surf, rect) = highlights[selected_idx]
#         screen.blit(surf, rect)
#     elif selected_idx is not None:
#         print("Turning off")
#         remove_border_from(screen, selected_idx)
#         selected_idx = None

    # # TODO get new display form server
    # pygame.display.flip()

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Start dragging when mouse button is pressed
        if event.type == pygame.MOUSEBUTTONDOWN:
            print(f"Selected is {selected}")
            
            # Check if selecting one of our cards
            for i, (card, card_rect) in enumerate(my_cards):
                if card_rect.collidepoint(event.pos):  # Check if mouse is on one of our cards
                    if selected:
                        # Turn off highlight
                        remove_border_from(screen, selected_idx)
                        selected_idx = None
                    
                    selected = True

                    selected_idx = i
                    print(f"Selected {card}")
                    break

            if selected:
                print(f"Else Case")
                for i, (card, card_rect) in enumerate(mid_decks):
                    print(card_rect, event.pos)
                    if card_rect.collidepoint(event.pos):  # Check if mouse is on one of our cards
                        selected = False
                        mid_decks[i] = (my_cards[selected_idx][0], card_rect)
                        print(f"Attempt to place")
                        ### Tell server we try a move ### 
                        screen.blit(*mid_decks[i])

                        break