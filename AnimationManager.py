import pygame
import time
import threading

class AnimationJob():
    """
    Symbolic representation of moving a card from one position to another.
    """
    def __init__(self, startPos, endPos, duration, screen, cardToMove, cardToCover):
        self.finished = False
        self.startPos = startPos
        self.endPos   = endPos
        
        self.cardToMove  = cardToMove
        self.rect        = cardToMove.get_rect(center = startPos)
        self.screen      = screen
        self.cardToCover = cardToCover
        self.rectToCover = cardToCover.get_rect(center = endPos)

        self.duration  = duration
        self.startTime = None


    def step(self):
        """
        Advance this animation by one timestep
        """
        # Start job at time of first tick 
        if not self.startTime:
            self.startTime = time.time()

        elapsed = time.time() - self.startTime
        prog    = min(elapsed / self.duration, 1) # Percent through animation

        # Update pos
        newX = self.startPos[0] + (self.endPos[0] - self.startPos[0]) * prog
        newY = self.startPos[1] + (self.endPos[1] - self.startPos[1]) * prog

        self.rect.center = (newX, newY)
        self.screen.blit(self.cardToCover, self.rectToCover)
        self.screen.blit(self.cardToMove, self.rect)

        if prog >= 1:
            self.finished = True
            print(f"{(newX, newY)} == {self.endPos}")

class AnimationManager():
    def __init__(self):
        self.jobs = []
        self.jobLock = threading.Lock()
        self.thisFrameJobCt = 0
        self.lastFrameJobCt = 0

    def register_job(self, job):
        with self.jobLock:
            self.jobs.append(job)

    def step_jobs(self):
        with self.jobLock:
            # print(f"Stepping {len(self.jobs)} jobs")
            [j.step() for j in self.jobs]
            self.jobs = [j for j in self.jobs if not j.finished]
            self.lastFrameJobCt = self.thisFrameJobCt
            self.thisFrameJobCt = len(self.jobs)
            
    def all_animations_stopped(self):
        return self.lastFrameJobCt > 0 and self.thisFrameJobCt == 0