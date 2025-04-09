from abc import ABC, abstractmethod
import time

#==============================================================================#
#                    Abstract base class for animation jobs                    #
#==============================================================================#
class BaseAnimationJob(ABC):
    def __init__(self):
        """
        Constructor

        Notes
        -----
        Establishes state variables needed for all Animation jobs:
        finished: bool
            Flag representing whether we have finished with this animation
        subordinates : list(BaseAnimationJob)
            List of jobs that we want to finish with us
        """
        self.finished = False
        self.subordinates = []

    @abstractmethod
    def step(self):
        """
        Advance animation by one frame

        Notes
        -----
        Must be implemeted by any class derived from this one.
        """
        pass

    def add_subordinate(self, subordinate):
        """
        Add a job that we will force to finish when we finish

        Parameters
        ----------
        subordinate: BaseAnimationJob
            The job to kill when we are done with this animation. The job's 
            .finish() function will be called.
        """
        self.subordinates.append(subordinate)

    def finish(self):
        """
        Flag this job as finished and stop and subordinates we have

        Notes
        -----
        Unless overridden, this will stop our subordinates, their subordinates,
        and so-on.
        """
        self.finished = True
        for job in self.subordinates:
            job.finish()

#==============================================================================#
# Subclasses of BaseAnimationJob
#==============================================================================#

class ShowImage(BaseAnimationJob):
    """
    This animation job puts an image at position pos on the screen until someone
    calls its finish() method
    """
    def __init__(self, screen, image, pos):
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
        super().__init__()
        self.pos = pos
        self.image = image
        self.rect = image.get_rect(center = pos)
        self.screen = screen

    def step(self):
        """
        Show image at position pos
        Overriden from BaseAnimationJob
        """
        self.screen.blit(self.image, self.rect)

class LinearMove(BaseAnimationJob):
    """
    Moves an image from startPos to endPos over length of time duration
    """
    def __init__(self, startPos, endPos, duration, screen, img):
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
        super().__init__()
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
