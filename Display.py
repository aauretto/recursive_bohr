"""
Display.py
Authors: Aiden Auretto, Peter Scully, Simon Webber, Claire Williams
Date: 4/28/2025

Purpose
------- 
    Drives the display and associated logic for said display and client
    interaction with that display
"""
import pygame 
from SharedState import ClientState, PlayCardAction
import math
from queue import Queue
from JobManager import *
import Animations
import os
from enum import Enum
from threading import Lock

FPS = 60
CARD_DIR = './images/card_pngs/'
HIGHLIGHT_COLOR = (180, 0, 180)
FONT_SIZE = 30
VERT_DIVS = 6
OPP_VERT_POS = 5
MID_VERT_POS = 3
MY_VERT_POS = 1

class Display():

    class DisplayStatusValue(Enum):
        """
        The possible statuses Display can have
        """
        SETUP = 0
        RUNNING = 1
        STOPPING = 2

    class DisplayStatus:
        """
        A monitor for DisplayStatusValue that also ensures we 
        cannot be unstopped
        """
        def __init__(self):
            """
            Constructor
            """
            self.__lock = Lock()
            self.__status = Display.DisplayStatusValue.SETUP

        def update_status(self, status):
            """
            Update the DisplayStatus as long as it hasn't already been stopped

            Parameters
            ----------
            status: Display.DisplayStatusValue
                The new display status
            """
            with self.__lock:
                if self.__status != Display.DisplayStatusValue.STOPPING:
                    self.__status = status
        
        def get_status(self):
            """
            Getter for the current display status

            Returns
            -------
            : Display.DusplayStatusValue
                the current display status
            """
            with self.__lock:
                return self.__status

    #*********************************************************************#
    #                      Constructor and Destructor                     #
    #*********************************************************************#

    def __init__(self, clientGame: ClientState, 
                 msgQueue: Queue, screenWidth = 1000, 
                 screenHeight = 800, backgroundColor=(30, 92, 58)):
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
        self.__gameState = clientGame
        self.__msgQueue = msgQueue
        self.__width = screenWidth
        self.__height = screenHeight
        self.__backgroundColor = backgroundColor

        # Initialize other internal variables
        self.__targetCardWidth = self.__width // 10
        self.__names = None
        self.__status = Display.DisplayStatus()

        # Create animation manager that handles drawing and moving cards
        self.__animationManager = JobManager()
        self.__animationManager.create_topic("static", 0)
        self.__animationManager.create_topic("dynamic", 1)
        self.__animationManager.create_topic("splashes", 2)

        # Create the dict for looking up the images of the cards
        self.__cardLookup = self.__create_card_img_dict()


        self.__vpos = {
                      "them" : self.__height - (OPP_VERT_POS * (self.__height)) 
                                             // (VERT_DIVS),
                      "mid"  : self.__height - (MID_VERT_POS * (self.__height)) 
                                             // (VERT_DIVS),
                      "me"   : self.__height - (MY_VERT_POS * (self.__height)) 
                                             // (VERT_DIVS),
                    }
        
        # Get the initial state of the game to display card x positions 
        # correctly
        self.__nMidPiles, self.__nTheirPiles, self.__nMyPiles \
            = self.__gameState.shape()
        self.__xpos = None
        self.__pile_xpos()

        # Gets populated by card objects each pass of the run loop
        self.__cardObjs = {
                          "them" : [],
                          "me"   : [],
                          "mid"  : [],
                        }

        # Finalize pygame initialization
        self.__screen = pygame.display.set_mode((self.__width, self.__height))
        pygame.display.set_caption(f"Spit!") # Default caption
        self.__clock = pygame.time.Clock()

    def __del__(self):
        """
        Used to initialize the member layouts the first time
        """
        pygame.quit()

    #*********************************************************************#
    #         Internal initializers of the cards that can be drawn        #
    #*********************************************************************#

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
                            (img.get_width() //
                             math.ceil(img.get_width() /
                                    self.__targetCardWidth), 
                             img.get_height() //
                             math.ceil(img.get_width() / 
                                    self.__targetCardWidth)))
        return img

    #*********************************************************************#
    #               Functions which display specific states               #
    #*********************************************************************#

    def run(self):
        """
        Wrapper for all the initial displaying and game loop
        """
        self.__show_first_frame()

        if self.__status.get_status() != Display.DisplayStatusValue.STOPPING:
            caption = "Playing Spit! with "
            for i, name in enumerate(self.__names):
                caption += name
                if i < len(self.__names) - 1:
                    caption += ", "
        
            pygame.display.set_caption(caption)
            self.__do_countdown()
            self.__run()   

    def __show_first_frame(self):
        """
        Set up the initial frame (waiting for opponent) while allowing the 
        player to quit
        """

        # Manager for the animations in this screen only
        waitingManager = JobManager() 
        waitingManager.create_topic("splashes", 0)
        
        # Show gray screen with "waiting for opponent" on it:
        waitingManager.register_job(
            Animations.OverlayAndText(self.__screen, 
                                      (128,128,128,200), 
                                      "Waiting for Opponent...",
                                      (self.__width // 2, 270)), 
                                    "splashes")
    
        # Run a loop that displays the screen and lets the user quit
        while self.__status.get_status() == Display.DisplayStatusValue.SETUP:
            self.__clock.tick(FPS)
            self.__screen.fill(self.__backgroundColor)

            waitingManager.step_jobs()

            # Allow player to quit but no other interaction
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    self.__status.update_status(
                        Display.DisplayStatusValue.STOPPING)
                    self.__msgQueue.put(("quitting",))
                    return
            pygame.display.flip()
        
    def __do_countdown(self, duration = 3):
        """
        Display initial countdown screen
        
        Parameters
        ----------
        duration: float
            Time in s for the countdown to last. (will countdown from 3 
            regardless of value of duration with the time between each digit
            being duration / 3)
        """

        # Custom manager so we dont muck with animation manager for this class
        countDownManager = JobManager()
        countDownManager.create_topic("splashes")

        # Image to show when countdown is over
        goImg = pygame.image.load("./images/go.png")
        goImg = pygame.transform.scale(goImg, (600,450))

        # Each "showX" job displays a digit and queues the next digit to 
        # display after a third of the countdown has passed
        show3inner = Animations.OverlayAndText(self.__screen, 
                                               (0,0,0,0), 
                                               "3", 
                                               (self.__width // 2 - 100, 260),
                                               textColor=(255,0,0))
        show2inner = Animations.OverlayAndText(self.__screen, 
                                               (0,0,0,0), 
                                               "2", 
                                               (self.__width // 2, 260),
                                               textColor=(255,0,0))
        show1inner = Animations.OverlayAndText(self.__screen, 
                                               (0,0,0,0), 
                                               "1", 
                                               (self.__width // 2 + 100, 260),
                                               textColor=(255,0,0))
        showGo = Animations.GrowAndFadeAnimation(self.__screen, 
                                                 (self.__width // 2, 
                                                 self.__height // 2), 
                                                 goImg, 
                                                 1, 
                                                 startImmediately=False)

        # Link all jobs so that we count 3 -> 2 -> 1 -> GO! then remove them 
        # all when we are done
        show1 = JobWithTrigger(show1inner, DELAY_TRIGGER(duration/3), 
                               lambda: show1.finish(), 
                               startImmediately=False, triggerOnce=True)
        show2 = JobWithTrigger(show2inner, DELAY_TRIGGER(duration/3), 
                               lambda: show1.start(), 
                               startImmediately=False, triggerOnce=True)
        show3 = JobWithTrigger(show3inner, DELAY_TRIGGER(duration/3), 
                               lambda: show2.start(), 
                               startImmediately=True, triggerOnce=True)
        show1.add_successor(showGo)
        show1.add_dependent(show2)
        show1.add_dependent(show3)

        # Send jobs to manager
        countDownManager.register_job(show3,  "splashes")
        countDownManager.register_job(show2,  "splashes")
        countDownManager.register_job(show1,  "splashes")
        countDownManager.register_job(showGo, "splashes")

        # Loop that shows initial state and a countdown
        while not countDownManager.all_animations_stopped() and \
              self.__status.get_status() != Display.DisplayStatusValue.STOPPING:
            
            # Background and cards
            self.__clock.tick(FPS)
            self.__screen.fill(self.__backgroundColor)
            self.__update_layouts()

            # Countdown animations
            countDownManager.step_jobs()

            # Allow players to quit but no other interaction
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    self.__status.update_status(
                        Display.DisplayStatusValue.STOPPING)
                    self.__msgQueue.put(("quitting",))
                    return
            pygame.display.flip()

    def __run(self):
        """
        Runs the display loop that accepts player interaction
        """
        # Tells us which cards are selected
        selected = False
        selectedIdx = None

        while self.__status.get_status() != Display.DisplayStatusValue.STOPPING:
            # Handle intializing the frame
            self.__clock.tick(FPS)
            self.__screen.fill(self.__backgroundColor) # Draw background

            # Handle visualization of player selecting a card
            selectable = self.__update_layouts()
            self.__do_highlight(selected, selectedIdx)

            self.__animationManager.step_jobs()
            if self.__animationManager.all_animations_stopped():
                self.__msgQueue.put(("done-moving",))

            # Event Loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Stops sender and sends out quitting msg to server
                    self.__msgQueue.put(("quitting",))
                    self.stop_display()

                # Select card when mouse button is pressed
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Check if selecting one of our cards
                    for i, (_, card_rect) in enumerate(self.__cardObjs["me"]):
                        # Check if mouse is on one of our cards
                        if card_rect.collidepoint(event.pos) and \
                            selectable[i]:  
                            selected = True
                            selectedIdx = i
                            break

                    if selected:
                        # Check if we are trying to place a card
                        for i, (card, card_rect) in \
                            enumerate(self.__cardObjs["mid"]):
                            # Check if mouse is on one of our cards
                            if card_rect.collidepoint(event.pos): 
                                selected = False
                                self.__msgQueue.put(('play', 
                                                     PlayCardAction(
                                                         selectedIdx, i)))

                                break
                            
            pygame.display.flip()

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
        image = pygame.transform.scale(image, 
                                       (self.__width // 2, self.__height // 2))
        rect  = image.get_rect(center = (self.__width // 2, self.__height // 2))

        # Put the image on the screen
        self.__screen.blit(image, rect)
        pygame.display.flip()

        # Wait for the user to quit
        quit=False
        while not quit:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit = True
        pygame.quit()

    #*********************************************************************#
    #    Functions for the Display owner to update internal info safely   #
    #*********************************************************************#

    def set_initial(self):
        """
        Used to initialize the member layouts the first time
        """
        self.__update_layouts()

    def set_names(self, names):
        """
        Updates the names of who is playing
        """
        self.__names = names

    #*********************************************************************#
    #          Internal updaters of what should be drawn and where        #
    #*********************************************************************#

    def __update_layout(self, layout, who):
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
        imgs = [self.__cardLookup[str(c)] for c in layout]
        self.__cardObjs[who] = [(card, card.get_rect()) for card in imgs]

        for i in range(len(self.__cardObjs[who])):
            (card, cardRect) = self.__cardObjs[who][i]
            cardRect.center = (self.__xpos[who][i], self.__vpos[who])
            self.__screen.blit(card, cardRect)
    
    def __update_layouts(self):
        # Make and place the cards on the screen
        myLayout, theirLayout, midPiles, selectable, myCardsLeft, \
            theirCardsLeft = self.__gameState.get_state()

        self.__pile_xpos() # update sizes of each set of piles

        self.__update_layout(myLayout, "me")
        self.__update_layout(theirLayout, "them")
        self.__update_layout(midPiles, "mid")

        # Show cards left
        self.__show_cards(myCardsLeft, self.__height - FONT_SIZE)
        self.__show_cards(theirCardsLeft, FONT_SIZE)

        return selectable

    def __pile_xpos(self):
        """
        Updates the horizontal positions of the cards based on the current
        shape of the game
        """
        self.__nMyPiles, self.__nTheirPiles, self.__nMidPiles = \
            self.__gameState.shape()
        self.__xpos = {
                   "them" : [i * (self.__width // (self.__nTheirPiles + 1)) 
                             for i in range(1, self.__nTheirPiles + 1)],
                   "me"   : [i * (self.__width // (self.__nMyPiles + 1))    
                             for i in range(1, self.__nMyPiles + 1)],
                   "mid"  : [i * (self.__width // (self.__nMidPiles + 1))   
                             for i in range(1, self.__nMidPiles + 1)],
               }

    def __show_cards(self, num, height):
        """
        Displays the count of cards left in a deck

        Parameters
        ----------
        num: int
            The number of cards remaining
        height: int
            The distance in pixels the center of the text will appear from the 
            top of the screen
        """
        # Set up font

        font = pygame.font.SysFont(None, FONT_SIZE)  
        # None = default font, 72 = size

        # Get rect to center it
        # True = anti-aliasing
        text_surface = font.render(f"Cards Remaining: {num}", True, (0, 0, 0))  
        text_rect = text_surface.get_rect(center=(self.__width // 2, height))
        self.__screen.blit(text_surface, text_rect)

    def __do_highlight(self, selected, selectedIdx):
        """
        Show the highlighting of the selected card

        Parameters
        ----------
        selected: bool
            Whether a card should be selected or not
        selectedIdx: int
            The index of the selected card in out layout
        """
        highlights = []
        for (_, rect) in self.__cardObjs["me"]:
            highlights.append(self.__make_border(10, .5, rect, HIGHLIGHT_COLOR))
        if selected:
            (surf, rect) = highlights[selectedIdx]
            self.__screen.blit(surf, rect)

    def __make_border(self, rect_add, cntr_offset, rect, color, width = 5):
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
        surf = pygame.Surface((rect.w + rect_add, rect.h + rect_add), 
                              pygame.SRCALPHA)  
        # Transparent center
        hl_rect = pygame.draw.rect(surf, color, 
                                   (0, 0, rect.width + rect_add, 
                                    rect.height + rect_add), 
                                   width = width)
        hl_rect.center = (rect.center[0] + cntr_offset, 
                          rect.center[1] + cntr_offset)
        return surf, hl_rect

    #*********************************************************************#
    #                Functions to add special animations                 #
    #*********************************************************************#

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
        # Get the flip image, scale it to the max size we want it to show as
        middle = (self.__width // 2, self.__height // 2)
        img = pygame.image.load("./images/flip.png")
        szW, szH = img.get_size()
        img = pygame.transform.scale(img, (szW * 2, szH * 2))

        # Create the flip animation and register it
        flipAnimation = Animations.GrowAndFadeAnimation(self.__screen, middle, 
                                                        img, 1)
        self.__animationManager.register_job(flipAnimation, "splashes")

        # Loop through the cards (and their locations) that are being flipped
        for (card, pileIdx) in zip(cards, pileIdxs):
            
            # Get images and locations needed for this animation. When we flip 
            # we hold the old card over the position we are flipping into and 
            # move the new card from the side of the screen to cover it.
            # This lets us see the card that was in the middle pile get covered
            # correctly.
            oldImg, _ = self.__cardObjs["mid"][pileIdx]
            newImg = self.__cardLookup[str(card)]
        
            destYpos = self.__vpos["mid"]
            destXpos = self.__xpos["mid"][pileIdx]

            # Determine starting position of card
            sideParity = -1 if pileIdx < self.__nMidPiles / 2 else 1
            srcYpos = self.__vpos["mid"]
            srcXpos = ((self.__width // 2) + sideParity * 0.5 
                      * (self.__width + newImg.get_width()))
            
            # Create an animation that moves new card into middle and one that
            # shows old card on top of current middle pile so that we don't
            # see state update immediately. Make the animation that shows
            # the old card stop when the new card has covered it completely.
            job = Animations.LinearMove((srcXpos, srcYpos), 
                                        (destXpos, destYpos), 
                                        duration, 
                                        self.__screen, 
                                        newImg)
            holdJob = Animations.ShowImage(self.__screen, 
                                           oldImg, 
                                           (destXpos, destYpos))
            job.add_dependent(holdJob)
            self.__animationManager.register_job(job, "dynamic")
            self.__animationManager.register_job(holdJob, "static")

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
        # TODO AIDEN
        srcYpos = self.__vpos[src]
        srcXpos = self.__xpos[src][srcPile]

        destYpos = self.__vpos[dest]
        destXpos = self.__xpos[dest][destPile]

        cardToMove, _ = self.__cardObjs[src][srcPile]
        cardToCover, _ = self.__cardObjs[dest][destPile]
        holdJob = Animations.ShowImage(self.__screen, cardToCover, (destXpos, 
                                                                    destYpos))
        moveJob = Animations.LinearMove((srcXpos, srcYpos), 
                                        (destXpos, destYpos), duration, 
                                        self.__screen, cardToMove)
        moveJob.add_dependent(holdJob)
        self.__animationManager.register_job(moveJob, "dynamic")
        self.__animationManager.register_job(holdJob, "static", 
                                             TopicOrder.BEFORE)

    def bad_move(self, pileIdx):
        """
        Shows a not_allowed indicator below the pile

        Parameters
        ----------
        pileIdx: int
            The index of the midPile below which the not_allowed image will be
            drawn
        """
        img = pygame.image.load("./images/not_allowed.png")
        img = pygame.transform.scale(img, (50,50))

        # Show image below the mid-pile we tried to play on
        xpos = self.__xpos["mid"][pileIdx]
        ypos = self.__vpos["mid"] + 100
        showX = Animations.ShowImage(self.__screen, img, (xpos,ypos), 
                                     duration=0.5)
        self.__animationManager.register_job(showX, "static")
    
    #*********************************************************************#
    #              Functions to transition the Display status             #
    #*********************************************************************#
    def done_setup(self):
        """
        Set the display status to be running
        """
        self.__status.update_status(Display.DisplayStatusValue.RUNNING)
        self.__msgQueue.put(('done-moving',))
    
    def stop_display(self):
        """
        Updates the dispaly status to stopping, effectively starting the 
        shutdown process for the running display
        """
        self.__status.update_status(Display.DisplayStatusValue.STOPPING)
    