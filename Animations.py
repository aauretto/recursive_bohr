"""
File: Animation.py
Authors: Aiden Auretto, Peter Scully, Simon Webber, Claire Williams
Date: 4/28/2025

Purpose
------- 
    Definitions for animation classes used in Display to draw animations on the
    screen at runtime. All of the classes in this file extend JobManager.BaseJob
    and are meant to be registered to a JobManager.
"""

import time
import pygame
from JobManager import BaseJob, JobWithTrigger

#==============================================================================#
#                     Subclasses of BaseJob Used for Animations
#==============================================================================#

class ShowImage(BaseJob):
    """
    This animation job puts an image at position pos on the screen until someone
    calls its finish() method
    """
    def __init__(self, screen, image, pos, startImmediately=True, 
                 duration=None):
        """
        Constructor

        Parameters
        ----------
        screen: pygame.display
            The screen on which to draw our animation
        image: pygame.image
            The image to display
        pos: tuple(int, int)
            The center (x,y) position in pixels to display the image at
        """
        super().__init__(startImmediately)
        self.__image = image
        self.__rect = image.get_rect(center = pos)
        self.__screen = screen
        self.__startTime = None
        self.__duration = duration

    def step(self):
        """
        Show image at position pos
        Overriden from BaseJob
        """
        if self.__startTime is None:
            self.__startTime = time.time()
        
        self.__screen.blit(self.__image, self.__rect)
        
        if self.__duration is not None and \
           time.time() - self.__startTime >= self.__duration:
                self.finish()

class LinearMove(BaseJob):
    """
    Moves an image from startPos to endPos over length of time duration
    """
    def __init__(self, startPos, endPos, duration, screen, img, 
                 startImmediately=True):
        """
        Constructor

        Parameters
        ----------
        startPos: tuple(int, int)
            The (x,y) position in pixels to start the animation at
        endPos: tuple(int, int)
            The (x,y) position in pixels to end the animation at
        duration: float
            The time in s the image takes to move from startPos to endPos
        screen: pygame.display
            The screen on which to draw our animation
        img: pygame.image
            The image to draw on our screen
        """
        super().__init__(startImmediately)
        self.__startPos = startPos
        self.__endPos   = endPos
        
        self.__img    = img
        self.__rect   = img.get_rect(center = startPos)
        self.__screen = screen

        self.__duration  = duration
        self.__startTime = None

    def step(self):
        """
        Move image from one part of the screen to another.
        Each call to .step() advances the animation by one frame.
        """
        # Start job at time of first tick
        if not self.__startTime:
            self.__startTime = time.time()

        # Percent through animation
        elapsed = time.time() - self.__startTime
        prog    = min(elapsed / self.__duration, 1) 

        # Update pos
        newX = self.__startPos[0] + (self.__endPos[0] - self.__startPos[0]) * \
            prog
        newY = self.__startPos[1] + (self.__endPos[1] - self.__startPos[1]) * \
            prog

        # Draw image in new pos
        self.__rect.center = (newX, newY)
        self.__screen.blit(self.__img, self.__rect)

        if prog >= 1:
            self.finish()

class GrowAndFadeAnimation(BaseJob):
    """
    Grows and fades an image over time
    """
    def __init__(self, screen, pos, img, duration, startImmediately=True):
        """
        Constructor

        Parameters
        ----------
        screen: pygame.display
            The screen on which to draw our animation
        pos: tuple(int, int)
            The screen location of the center of the image
        img: pygame.image
            The image to draw on our screen
        duration: float
            The time in s the image takes to move from startPos to endPos
        startImmediately: bool
            Whether the flip should start immediately or will need to be
            triggered by another job
        """
        super().__init__(startImmediately)
        self.__pos = pos
        
        self.__img       = img
        self.__startSize = img.get_size()
        
        self.__screen    = screen
        self.__duration  = duration
        self.__startTime = None

    def step(self):
        """
        Grows the image from a single point to its full size while
        fading it out
        """
        # Start job at time of first tick
        if not self.__startTime:
            self.__startTime = time.time()

        # Percent through animation
        elapsed = time.time() - self.__startTime
        prog    = min(elapsed / self.__duration, 1) 

        # Update size
        dimX = self.__startSize[0] * prog
        dimY = self.__startSize[1] * prog

        # Draw image in new pos
        tmpImg = pygame.transform.scale(self.__img, (dimX, dimY))
        tmpImg.set_alpha(255 * (1 - prog))
        self.__screen.blit(tmpImg, tmpImg.get_rect(center = self.__pos))

        if prog >= 1:
            self.finish()


class OverlayAndText(BaseJob):
    """
    Puts a colored overlay on top of the entire screen and then displays some
    text in a given position
    """
    def __init__(self, screen, bgColor, text, textPos, fontSz = 72, 
                 textColor=(0,0,0), startImmediately=True):
        """
        Constructor

        Parameters
        ----------
        screen: pygame.display
            The screen on which to draw our animation
        bgColor: tuple(int, int, int, int)
            RGBA code for color to fill screen with__
        test: str
            Text to display
        textPos: tuple(int, int)
            The center (x,y) position in pixels to display the text at
        fontSz: int
            Font size to use
        textColor: tuple(int, int, int, int)
            RGBA code for text color
        startImmediately: bool
            Whether the flip should start immediately or will need to be
            triggered by another job
        """
        super().__init__(startImmediately)
        self.__screen = screen

        width = self.__screen.get_width()
        height = self.__screen.get_height()
        textXpos, textYpos = textPos

        self.__overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self.__overlay.fill(bgColor)
        font = pygame.font.SysFont(None, fontSz)
        
        # Get rect to center it
        # True = anti-aliasing
        self.__textSurf = font.render(text, True, textColor)
        self.__textRect = self.__textSurf.get_rect(center=(textXpos, textYpos))


    def step(self):
        """
        Paint overlay then put text on top of that
        """
        self.__screen.blit(self.__overlay, (0,0))
        self.__screen.blit(self.__textSurf, self.__textRect)