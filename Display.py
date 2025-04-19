import time
import pygame 
from SharedState import ClientState, PlayCardAction
import math
from queue import Queue
from JobManager import *
import Animations
import os
from enum import Enum

FPS = 60
CARD_DIR = './images/card_pngs/'
HIGHLIGHT_COLOR = (180, 0, 180)
FONT_SIZE = 30

class Display():

    class DisplayStatus(Enum):
        SETUP = 0
        RUNNING = 1
        STOPPING = 2

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
        backgroundColor: tuple(int, int, int)
            The RGB tuple for the color of the game's background
        """
 
         # Initialize pygame if it wasn't already
        if not pygame.get_init():
            pygame.init()
        
        # Inialize internal variables from parameters
        self.gameState = clientGame
        self.msgQueue = msgQueue
        self.width = screenWidth
        self.height = screenHeight
        self.backgroundColor = backgroundColor

        # Initialize other internal variables
        self.targetCardWidth = self.width // 10
        self.names = None
        self.status = Display.DisplayStatus.SETUP

        # Create animation manager that handles drawing and moving cards
        self.animationManager = JobManager()
        self.animationManager.create_topic("static", 0)
        self.animationManager.create_topic("dynamic", 1)
        self.animationManager.create_topic("splashes", 2)

        # Create the dict for looking up the images of the cards
        self.cardLookup = self.__create_card_img_dict()

        # TODO this needs to be fixed / documented / shaped
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

        # Finalize pygame initialization
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(f"Spit!") # Default caption
        self.clock = pygame.time.Clock()

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
        Used to initialize the member layouts the first time
        """
        pygame.quit()

    def set_names(self, names):
        """
        Destructor to gracefully close pygame
        """
        self.names = names

    def __create_card_img_dict(self):
        """
        Create the initial lookup dictionary for cards

        Returns
        -------
        cardDict: dict{str -> pygame.Surface}
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
                            (img.get_width() // \
                             math.ceil(img.get_width() / self.targetCardWidth), 
                             img.get_height() // \
                             math.ceil(img.get_width() / self.targetCardWidth)))
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
    
    def flip_cards(self, cards, pileIdxs, duration):
        """
        Queues animation jobs surrounding how flipping from the decks to the
        center piles is handled

        Parameters
        ----------
        cards: list(Card)
            The cards to flip
        pileIdxs: list(int)
            The indicies of the midpiles to flip each card on to. cards[i] goes
            onto pileIdxs[i]
        duration: float
            Time in seconds for each card to travel
        
        Returns
        -------
        None
        """
        # TODO inline comments
        middle = (self.width // 2, self.height // 2)
        img = pygame.image.load("./images/flip.png")
        szW, szH = img.get_size()
        img = pygame.transform.scale(img, (szW * 2, szH * 2))
        flipAnimation = Animations.FlipAnimation(self.screen, middle, img, 1)
        self.animationManager.register_job(flipAnimation, "splashes")

        for (card, pileIdx) in zip(cards, pileIdxs):

            oldImg, _ = self.cardObjs["mid"][pileIdx]
            newImg = self.cardLookup[str(card)]
        
            destYpos = self.vpos["mid"]
            destXpos = self.xpos["mid"][pileIdx]

            # Comes in from left or right?
            sideParity = -1 if pileIdx < self.nMidPiles / 2 else 1
            srcYpos = self.vpos["mid"]
            srcXpos = (self.width // 2) + sideParity * 0.5 * (self.width + newImg.get_width())
            
            job = Animations.LinearMove((srcXpos, srcYpos), (destXpos, destYpos), duration, self.screen, newImg)
            holdJob = Animations.ShowImage(self.screen, oldImg, (destXpos, destYpos))
            job.add_dependent(holdJob)
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
        moveJob.add_dependent(holdJob)
        self.animationManager.register_job(moveJob, "dynamic")
        self.animationManager.register_job(holdJob, "static", DrawOrder.BEFORE)

    def done_setup(self):
        """
        Set the display status to be running
        """
        self.status = Display.DisplayStatus.RUNNING

    def show_first_frame(self):
        """
        Set up the initial frame (all blank cards) and allow the player to quit
        """
        #TODO Aiden doc this
        waitingOverlay = Animations.OverlayAndText(self.screen, (128,128,128,200), "Waiting for Opponent...", (self.width // 2, 270))
        self.animationManager.register_job(waitingOverlay, "splashes")

        # Display the first frame 
        while self.status == Display.DisplayStatus.SETUP:
            self.clock.tick(FPS)
            pygame.display.flip()

            myLayout, theirLayout, midPiles, _, myCardsLeft, theirCardsLeft = self.gameState.get_state()

            self.screen.fill(self.backgroundColor)
            self.__update_layouts(myLayout, "me")
            self.__update_layouts(theirLayout, "them")
            self.__update_layouts(midPiles, "mid")

            # Show cards left
            self.__show_cards(myCardsLeft, self.height - FONT_SIZE)
            self.__show_cards(theirCardsLeft, FONT_SIZE)

            self.animationManager.step_jobs()

            # Allow player to quit but no other interaction
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    self.status = Display.DisplayStatus.STOPPING
                    self.msgQueue.put(("quitting",))
                    return
        
        waitingOverlay.finish()
        self.animationManager.remove_finished()
        print("Done showing initial frame")

    def do_countdown(self, duration = 3):
        # 3s Countdown by default

        # Custom manager so we dont muck with animation manager for this class
        countDownManager = JobManager()
        countDownManager.create_topic("splashes")

        # Each "showX" job displays a digit and queues the next digit to display after a third of the countdown has passed
        show3inner = Animations.OverlayAndText(self.screen, (0,0,0,0), "3", (self.width // 2 - 100, 260))
        show2inner = Animations.OverlayAndText(self.screen, (0,0,0,0), "2", (self.width // 2      , 260))
        show1inner = Animations.OverlayAndText(self.screen, (0,0,0,0), "1", (self.width // 2 + 100, 260))

        show1 = JobWithTrigger(show1inner, DELAY_TRIGGER(duration/3), lambda: show1.finish(), startImmediately=False, triggerOnce=True)
        show2 = JobWithTrigger(show2inner, DELAY_TRIGGER(duration/3), lambda: show1.start(), startImmediately=False, triggerOnce=True)
        show3 = JobWithTrigger(show3inner, DELAY_TRIGGER(duration/3), lambda: show2.start(), startImmediately=True, triggerOnce=True)

        show1.add_dependent(show2)
        show1.add_dependent(show3)

        countDownManager.register_job(show3, "splashes")
        countDownManager.register_job(show2, "splashes")
        countDownManager.register_job(show1, "splashes")

        startTime = time.time()
        while (time.time() - startTime) <= duration and self.status != Display.DisplayStatus.STOPPING:
            self.clock.tick(FPS)
            pygame.display.flip()

            myLayout, theirLayout, midPiles, _, myCardsLeft, theirCardsLeft = self.gameState.get_state()

            self.screen.fill(self.backgroundColor)
            self.__update_layouts(myLayout, "me")
            self.__update_layouts(theirLayout, "them")
            self.__update_layouts(midPiles, "mid")

            # Show cards left
            self.__show_cards(myCardsLeft, self.height - FONT_SIZE)
            self.__show_cards(theirCardsLeft, FONT_SIZE)

            countDownManager.step_jobs()

            # Allow players to quit but no other interaction
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    self.status = Display.DisplayStatus.STOPPING
                    self.msgQueue.put(("quitting",))
                    return


    def stop_display(self):
        """
        # TODO AIDEN
        """
        self.status = Display.DisplayStatus.STOPPING
        self.msgQueue.put(None) # TODO Don't love this, do we consider putting this where this funciton is called

    def run(self):
        """
        Runs the display loop that accepts player interaction
        """

        self.show_first_frame()


        if self.status != Display.DisplayStatus.STOPPING:
            caption = "Playing Spit! with "
            for i, name in enumerate(self.names):
                caption += name
                if i < len(self.names) - 1:
                    caption += ", "
        
            pygame.display.set_caption(caption)
            self.do_countdown()


        # ==========================================================
        # All initialization screen stuff should show up before here
        # ==========================================================
        
        # Tells us which cards are selected
        selected = False
        selectedIdx = None

        while self.status != Display.DisplayStatus.STOPPING:
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
                    # Stops sender and sends out quitting msg to server
                    self.msgQueue.put(("quitting",))
                    # TODO maybe call stop game
                    self.status = Display.DisplayStatus.STOPPING

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
                        # Check if we are trying to place a card
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
        rect: pygame.Rect
            The pygame rect around which to make a border
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
        """
        # TODO assess if we actually need this
        """
        (_, rect) = highlights[border_idx]
        surf, rect = self.make_border(0, 0, rect, self.backgroundColor)
        return surf, rect

    def remove_border_from(self, screen, highlights, border_idx):
        """
        # TODO also asses if we need this 
        """
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
        image = pygame.image.load(f"./images/{result}.png").convert_alpha()

        # Make the image half translucent
        image.set_alpha(128)

        # Scale and center the image
        image = pygame.transform.scale(image, (self.width // 2, self.height // 2))
        rect  = image.get_rect(center = (self.width // 2, self.height // 2))

        # Put the image on the screen
        self.screen.blit(image, rect)
        pygame.display.flip()

        # Wait for the user to quit
        quit=False
        while not quit:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit = True
        pygame.quit()