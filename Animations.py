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
    def __init__(self, screen, image, pos, startImmediately=True, duration=None):
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
        self.pos = pos
        self.image = image
        self.rect = image.get_rect(center = pos)
        self.screen = screen

    def step(self):
        """
        Show image at position pos
        Overriden from BaseJob
        """
        self.screen.blit(self.image, self.rect)

class LinearMove(BaseJob):
    """
    Moves an image from startPos to endPos over length of time duration
    """
    def __init__(self, startPos, endPos, duration, screen, img, startImmediately=True):
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
        self.startPos = startPos
        self.endPos   = endPos
        
        self.img    = img
        self.rect   = img.get_rect(center = startPos)
        self.screen = screen

        self.duration  = duration
        self.startTime = None

    def step(self):
        """
        Move image from one part of the screen to another.
        Each call to .step() advances the animation by one frame.
        """
        # Start job at time of first tick
        if not self.startTime:
            self.startTime = time.time()

        # Percent through animation
        elapsed = time.time() - self.startTime
        prog    = min(elapsed / self.duration, 1) 

        # Update pos
        newX = self.startPos[0] + (self.endPos[0] - self.startPos[0]) * prog
        newY = self.startPos[1] + (self.endPos[1] - self.startPos[1]) * prog

        # Draw image in new pos
        self.rect.center = (newX, newY)
        self.screen.blit(self.img, self.rect)

        if prog >= 1:
            self.finish()

class FlipAnimation(BaseJob):
    """
    Moves an image from startPos to endPos over length of time duration #TODO what does this actually do
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
        self.pos = pos
        
        self.img       = img
        self.startSize = img.get_size()
        
        self.screen    = screen
        self.duration  = duration
        self.startTime = None

    def step(self):
        """
        TODO: REAASONABLE DOCUMENTATION
        """
        # Start job at time of first tick
        if not self.startTime:
            self.startTime = time.time()

        # Percent through animation
        elapsed = time.time() - self.startTime
        prog    = min(elapsed / self.duration, 1) 

        # Update size
        dimX = self.startSize[0] * prog
        dimY = self.startSize[1] * prog

        # Draw image in new pos
        tmpImg = pygame.transform.scale(self.img, (dimX, dimY))
        tmpImg.set_alpha(255 * (1 - prog))
        self.screen.blit(tmpImg, tmpImg.get_rect(center = self.pos))

        if prog >= 1:
            self.finish()


class OverlayAndText(BaseJob):
    """
    Puts a colored overlay on top of the entire screen and then displays some
    text in a given position
    """
    def __init__(self, screen, bgColor, text, textPos, fontSz = 72, textColor = (0,0,0), startImmediately=True):
        """
        Constructor

        Parameters
        ----------
        screen: pygame.display
            The screen on which to draw our animation
        bgColor: tuple(int, int, int, int)
            RGBA code for color to fill screen with
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
        self.screen = screen

        width = self.screen.get_width()
        height = self.screen.get_height()
        textXpos, textYpos = textPos

        self.overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self.overlay.fill(bgColor)
        font = pygame.font.SysFont(None, fontSz)
        
        # Get rect to center it
        self.textSurf = font.render(text, True, textColor)  # True = anti-aliasing
        self.textRect = self.textSurf.get_rect(center=(textXpos, textYpos))


    def step(self):
        """
        Paint overlay then put text on top of that
        """
        self.screen.blit(self.overlay, (0,0))
        self.screen.blit(self.textSurf, self.textRect)