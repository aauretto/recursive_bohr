import pygame 
from SharedState import ClientState, PlayCardAction
import math
from queue import Queue
from AnimationManager import *
import Animations
import os

FPS = 60
CARD_DIR = './images/card_pngs/'
HIGHLIGHT_COLOR = (180, 0, 180)
FONT_SIZE = 30

class Display():
    def __init__(self, clientGame: ClientState, msgQueue: Queue, screenWidth = 1000, screenHeight = 800, backgroundColor=(30, 92, 58)):
        """
        A constructor for the display object

        Parameters
        ----------
        clientGame: ClientState
            The ClientState object from which we can access the relevant game
            information that we need
        msgQueue: Queue
            The queue onto which we push any information not handled by us
        screenWidth: int
            The width in pixels of the pygame screen the game will apear on
        screenHeight: int
            The height in pixels of the pygame screen the game will apear on
        
        """

        # Initialize pygame if it wasn't already and set a default caption
        if not pygame.get_init():
            pygame.init()
        pygame.display.set_caption("Spit")

        # Set the passed parameters to internal state variables
        self.gameState = clientGame
        self.msgQueue = msgQueue
        self.width = screenWidth
        self.height = screenHeight
        self.backgroundColor = backgroundColor

        # Set the target width of the cards to 1/10th the screen width
        self.targetCardWidth = self.width // 10

        # Create state variables to handle animations
        self.animationManager = AnimationManager()
        self.animationManager.create_topic("static", 0)
        self.animationManager.create_topic("dynamic", 1)

        # Creates the dictionary we use to get pygame card images and put them
        # on the screen
        self.cardLookup = self.__create_card_img_dict()

        # TODO fix these
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

        # Populate initial game state
        
        # Initialize the pygame screen the game will be plyed on
        self.screen = pygame.display.set_mode((self.width, self.height))

        self.clock = pygame.time.Clock()
        self.running = True

    def set_initial(self):
        """
        Used to initialize the member layouts the first time
        """
        myLayout, theirLayout, midPiles, _, _, _ = self.gameState.get_state()
        self.__update_layouts(myLayout, "me")
        self.__update_layouts(theirLayout, "them")
        self.__update_layouts(midPiles, "mid")

    def __del__(self):
        """
        Destructor to gracefully close pygame
        """
        pygame.quit()

    def __create_card_img_dict(self):
        
        """
        Creates the dictionary cardLookup mapping card names (as strings) to
        their pygame images (stored as Surfaces)

        Parameters: None
        
        Returns
        -------
        cardDict: dict{str --> Surface}
        """
        fileList = os.listdir(CARD_DIR)
        fileList = [f.strip(".png") for f in fileList]
        cardDict = {}
        for cardStr in fileList:
            cardDict[cardStr] = self.__card_to_pygame_img(cardStr)
        return cardDict
            



    def __card_to_pygame_img(self, card):
        """
        Converts a card into a pygame image of the card

        Parameters
        ----------
        card: str | Card
            The card to load as an image

        Returns
        -------
        img: pygame.Surface
            the pygame image of the card scaled so the width is as close to the 
            target width as possible
        """
        img = pygame.image.load(CARD_DIR + str(card) + '.png')
        img = pygame.transform.scale(img, 
                             (img.get_width() // math.ceil(img.get_width() \
                                                / self.targetCardWidth), 
                             img.get_height() // math.ceil(img.get_width() \
                                                / self.targetCardWidth)))
        return img

    def __update_layouts(self, layout, who):
        """
        Update the internal layout

        Parameters
        ----------
        layout: list(Card)
            The list of card objects in the relevant layout
        who: str
            Which layout we are talking about

        Return
        ------
        None
        
        """
        imgs = [self.cardLookup[str(c)] for c in layout]
        self.cardObjs[who] = [(card, card.get_rect()) for card in imgs]

        for i in range(len(self.cardObjs[who])):
            (card, cardRect) = self.cardObjs[who][i]
            cardRect.center = (self.xpos[who][i], self.vpos[who])
            self.screen.blit(card, cardRect)

    def get_ready(self, players):
        """
        Updates the pygame caption and waits for the player to be ready

        Parameters
        ----------
        players: list(str)
            The list of player names who are playing the game

        Notes
        -----
            Tells the the server we are ready after the player indicates so
        """
        print(f"Players in session: {players}")
        pygame.display.set_caption(f"Playing Spit! with: {players}")
        ready = 'n'
        while ready.strip()[0].lower() != 'y':
            ready = input(f"{players} have joined. Are you ready (y/n): ")
        self.msgQueue.put(('ready',))
    
    def flip_cards(self, oldPiles, newPiles, duration):
        """
        Queues animation jobs surrounding how flipping from the decks to the
        center piles is handled

        Parameters
        ----------
        oldPiles: # TODO Aiden
        """
        for i, (oldCard, newCard) in enumerate(zip(oldPiles, newPiles)):
            oldImg, _ = self.cardObjs["mid"][i]
            newImg = self.cardLookup[str(newCard)]
            # newImg = self.__card_to_pygame_img(newCard)
        
            destYpos = self.vpos["mid"]
            destXpos = self.xpos["mid"][i]

            srcYpos = self.vpos["mid"]
            srcXpos = (self.width // 2) + (2 * i - 1) * 0.5 * (self.width + newImg.get_width())
            
            
             # put 0.5 self.widths outside screen

            job = Animations.LinearMove((srcXpos, srcYpos), (destXpos, destYpos), duration, self.screen, newImg)
            holdJob = Animations.ShowImage(self.screen, oldImg, (destXpos, destYpos))
            job.add_subordinate(holdJob)
            self.animationManager.register_job(job, "dynamic")
            self.animationManager.register_job(holdJob, "static")

    def move_card(self, src, srcPile, dest, destPile, duration):
        """
        Moves a card from one pile onto another

        Parameters
        ----------
        src: str
            who owns the src piles
        srcPile: int
            The index of the source piles of the source card
        dest: str
            who own the destination piles
        destPile: int
            The index of the destination card in the destination piles
        duration: float
            The time in s the image takes to move from startPos to endPos

        Returns
        -------
        None 
        
        """
        # Calc start and end pos
        srcYpos = self.vpos[src]
        srcXpos = self.xpos[src][srcPile]

        destYpos = self.vpos[dest]
        destXpos = self.xpos[dest][destPile]

        cardToMove, _ = self.cardObjs[src][srcPile]
        cardToCover, _ = self.cardObjs[dest][destPile]
        holdJob = Animations.ShowImage(self.screen, cardToCover, (destXpos, destYpos))
        moveJob = Animations.LinearMove((srcXpos, srcYpos), (destXpos, destYpos), duration, self.screen, cardToMove)
        moveJob.add_subordinate(holdJob)
        self.animationManager.register_job(moveJob, "dynamic")
        self.animationManager.register_job(holdJob, "static", DrawOrder.BEFORE)

    def stop_display(self):
        """
        #TODO Aiden
        """
        self.running = False
        self.msgQueue.put(None)

    def run(self):
        """
        Runs the display loop that accepts player interaction
        """
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
        """
        Displays the count of cards left in a deck

        Parameters
        ----------
        num: int
            The number of cards remaining
        height: int
            The distance in pixels the center of the text will appear from the top of the screen
        """
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

        Returns
        -------
        surf, rect: (pygame.Surface, pygame.Rect)
            The surface and associated rect of the highlight
        """
        surf = pygame.Surface((rect.w + rect_add, rect.h + rect_add), pygame.SRCALPHA)
        hl_rect = pygame.draw.rect(surf, color, (0, 0, rect.width + rect_add, rect.height + rect_add), width = width)  # Transparent center
        hl_rect.center = (rect.center[0] + cntr_offset, rect.center[1] + cntr_offset)
        return surf, hl_rect

    def remove_border(self, highlights, border_idx):
        """
        # TODO assess if we actually need this
        """
        (_, rect) = highlights[border_idx]
        surf, rect = self.make_border(0, 0, rect, self.backgroundColor)
        return surf, rect

    def remove_border_from(self, screen, highlights, border_idx):
        surf, rect = self.remove_border(highlights, border_idx)
        screen.blit(surf, rect)

    def final_state(self, result):
        """
        Used to display the final state of the game

        Parameters
        ----------
        result: str
            the result of the game {won, lost, draw}

        Returns
        -------
        None
        """
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