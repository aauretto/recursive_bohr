import pygame 
from SharedState import ClientState, PlayCardAction
import math
from queue import Queue
from AnimationManager import *

FPS = 60
CARD_DIR = './images/card_pngs/'
HIGHLIGHT_COLOR = (180, 0, 180)
FONT_SIZE = 30

class Display():
    def __init__(self, clientGame: ClientState, msgQueue: Queue, screenWidth = 1000, screenHeight = 800, backgroundColor=(30, 92, 58)):
        if not pygame.get_init():
            pygame.init()
        pygame.display.set_caption("Spit")
        self.gameState = clientGame
        self.msgQueue = msgQueue

        self.animationManager = AnimationManager()
        self.animationManager.create_topic("static", 0)
        self.animationManager.create_topic("dynamic", 1)

        self.width = screenWidth
        self.height = screenHeight
        self.targetCardWidth = self.width // 10

        self.nMidPiles = 2
        self.nTheirPiles = 4
        self.nMyPiles = 4

        self.vpos = {
                      "them" : self.height - (5 * (self.height)) // (5 + 1),
                      "me"   : self.height - (1 * (self.height)) // (5 + 1),
                      "mid"  : self.height - (3 * (self.height)) // (5 + 1),
                    }
        
        self.xpos = {
                      "them" : [i * (self.width // (self.nTheirPiles + 1)) for i in range(1, self.nTheirPiles + 1)],
                      "me"   : [i * (self.width // (self.nMyPiles + 1))    for i in range(1, self.nMyPiles + 1)],
                      "mid"  : [i * (self.width // (self.nMidPiles + 1))   for i in range(1, self.nMidPiles + 1)],
                    }

        # Gets populated by card objects each pass of the run loop
        self.cardObjs = {
                          "them" : [],
                          "me"   : [],
                          "mid"  : [],
                        }

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(f"Spit!")
        self.backgroundColor = backgroundColor

        self.clock = pygame.time.Clock()
        self.running = True

    def __del__(self):
        pygame.quit()

    def __card_to_pygame_img(self, card):
        img = pygame.image.load(CARD_DIR + str(card) + '.png')
        img = pygame.transform.scale(img, 
                             (img.get_width() // math.ceil(img.get_width() \
                                                / self.targetCardWidth), 
                             img.get_height() // math.ceil(img.get_width() \
                                                / self.targetCardWidth)))
        return img

    def __update_layouts(self, layout, who):
        imgs = list(map(self.__card_to_pygame_img, layout))
        self.cardObjs[who] = [(card, card.get_rect()) for card in imgs]

        for i in range(len(self.cardObjs[who])):
            (card, cardRect) = self.cardObjs[who][i]
            cardRect.center = (self.xpos[who][i], self.vpos[who])
            self.screen.blit(card, cardRect)

    def get_ready(self, players):
        print(f"Players in session: {players}")
        ready = 'n'
        while ready.strip()[0].lower() != 'y':
            ready = input(f"{players} have joined. Are you ready (y/n): ")
        self.msgQueue.put(('ready',))
    
    def flip_cards(self, oldPiles, newPiles, duration):
        for i, (oldCard, newCard) in enumerate(zip(oldPiles, newPiles)):
            # oldImg = self.__card_to_pygame_img(oldCard)
            oldImg, _ = self.cardObjs["mid"][i]
            newImg = self.__card_to_pygame_img(newCard)
        
            destYpos = self.vpos["mid"]
            destXpos = self.xpos["mid"][i]

            srcYpos = self.vpos["mid"]
            srcXpos = (2 * i - 1) * self.width + 0.5 * self.width # put 0.5 self.widths outside screen

            job = LinearMoveAnimation((srcXpos, srcYpos), (destXpos, destYpos), duration, self.screen, newImg, oldImg)
            self.animationManager.register_job(job)

    def move_card(self, src, srcPile, dest, destPile, duration):
        # Calc start and end pos
        srcYpos = self.vpos[src]
        srcXpos = self.xpos[src][srcPile]

        destYpos = self.vpos[dest]
        destXpos = self.xpos[dest][destPile]

        cardToMove, _ = self.cardObjs[src][srcPile]
        cardToCover, _ = self.cardObjs[dest][destPile]
        holdJob = StaticHoldAnimation((destXpos, destYpos), self.screen, cardToCover)
        moveJob = LinearMoveAnimation((srcXpos, srcYpos), (destXpos, destYpos), duration, self.screen, cardToMove)
        moveJob.add_subordinate(holdJob)
        self.animationManager.register_job(moveJob, "dynamic")
        self.animationManager.register_job(holdJob, "static", DrawOrder.BEFORE)



    def stop_display(self):
        self.running = False
        self.msgQueue.put(None)

    def run(self):
        # Tells us which cards are selected
        selected = False
        selectedIdx = None

        while self.running:
            self.clock.tick(FPS)

            # Draw BG
            self.screen.fill(self.backgroundColor)

            # Make and place the cards on the screen
            myLayout, theirLayout, midPiles, selectable, myCardsLeft, theirCardsLeft = self.gameState.get_state()

            self.__update_layouts(myLayout, "me")
            self.__update_layouts(theirLayout, "them")
            self.__update_layouts(midPiles, "mid")

            # Show cards left
            self.__show_cards(myCardsLeft, self.height - FONT_SIZE)
            self.__show_cards(theirCardsLeft, FONT_SIZE)

            # Handle visualization of player selecting a card
            highlights = []
            for (_, rect) in self.cardObjs["me"]:
                highlights.append(self.make_border(10, .5, rect, HIGHLIGHT_COLOR))
            
            if selected:
                (surf, rect) = highlights[selectedIdx]
                self.screen.blit(surf, rect)
            elif selectedIdx is not None:
                self.remove_border_from(self.screen, highlights, selectedIdx)
                selectedIdx = None

            self.animationManager.step_jobs()

            # Only want to flip when nothing is going on
            if self.animationManager.all_animations_stopped():
                self.msgQueue.put(("no-animations",))

            # Event Loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.msgQueue.put(("quitting",))
                    
                    self.running = False

                # Select card when mouse button is pressed
                if event.type == pygame.MOUSEBUTTONDOWN:
                    print(f"Selected is {selected}")
                    
                    # Check if selecting one of our cards
                    for i, (card, card_rect) in enumerate(self.cardObjs["me"]):
                        if card_rect.collidepoint(event.pos) and selectable[i]:  # Check if mouse is on one of our cards
                            if selected:
                                # Turn off highlight
                                self.remove_border_from(self.screen, highlights, selectedIdx)
                                selectedIdx = None
                            
                            selected = True

                            selectedIdx = i
                            print(f"Selected {card}")
                            break

                    if selected:
                        print(f"Else Case")
                        for i, (card, card_rect) in enumerate(self.cardObjs["mid"]):
                            print(card_rect, event.pos)
                            if card_rect.collidepoint(event.pos):  # Check if mouse is on one of our cards
                                selected = False
                                self.msgQueue.put(('play', PlayCardAction(selectedIdx, i)))

                                break
                            
            pygame.display.flip()

    def __show_cards(self, num, height):
        # Set up font

        font = pygame.font.SysFont(None, FONT_SIZE)  # None = default font, 72 = size

        # Get rect to center it
        text_surface = font.render(f"Cards Remaining: {num}", True, (0, 0, 0))  # True = anti-aliasing
        text_rect = text_surface.get_rect(center=(self.width // 2, height))
        self.screen.blit(text_surface, text_rect)

    def make_border(self, rect_add, cntr_offset, rect, color, width = 5):
        """
        Creates a border

        Parameters
        ----------
        rect_add : int
            The amount around the rect to border
        cntr_offset : int
            The offset of the border center to the rect center
        color : (int, int, int)
            An RGB tuple for the color of the rectangle
        width : int
            The border width
        """
        surf = pygame.Surface((rect.w + rect_add, rect.h + rect_add), pygame.SRCALPHA)
        hl_rect = pygame.draw.rect(surf, color, (0, 0, rect.width + rect_add, rect.height + rect_add), width = width)  # Transparent center
        hl_rect.center = (rect.center[0] + cntr_offset, rect.center[1] + cntr_offset)
        return surf, hl_rect

    def remove_border(self, highlights, border_idx):
        (_, rect) = highlights[border_idx]
        surf, rect = self.make_border(0, 0, rect, self.backgroundColor)
        return surf, rect

    def remove_border_from(self, screen, highlights, border_idx):
        surf, rect = self.remove_border(highlights, border_idx)
        screen.blit(surf, rect)

    def final_state(self, result):
        # image = pygame.image.load(f"./images/{result}.png").convert_alpha()
        image = pygame.image.load(f"./images/won.png").convert_alpha()
        image.set_alpha(128)
        image = pygame.transform.scale(image, (self.width // 2, self.height // 2))
        rect  = image.get_rect(center = (self.width // 2, self.height // 2))
        self.screen.blit(image, rect)
        pygame.display.flip()
        quit=False
        while not quit:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit = True
        pygame.quit()