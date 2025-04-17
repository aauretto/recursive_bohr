import pygame
import threading
from enum import Enum
from abc import ABC, abstractmethod

#==============================================================================#
#                    Abstract base class for jobs                    #
#==============================================================================#
class BaseJob(ABC):
    def __init__(self, startImmediately=True):
        """
        Constructor

        Notes
        -----
        Establishes state variables needed for all Animation jobs:
        finished: bool
            Flag representing whether we have finished with this animation
        dependents : list(BaseAnimationJob)
            List of jobs that we want to finish with us
        """
        self.started = startImmediately
        self.finished = False
        self.successors = []
        self.dependents = []

    @abstractmethod
    def step(self):
        """
        Advance animation by one frame

        Notes
        -----
        Must be implemeted by any class derived from this one.
        """
        pass

    def add_dependent(self, job):
        """
        Add a job that we will force to finish when we finish

        Parameters
        ----------
        dependent: BaseAnimationJob
            The job to kill when we are done with this animation. The job's 
            .finish() function will be called.
        """
        self.dependents.append(job)

    def add_successor(self, job):
        """
        Add a job that we will start when we finish

        Parameters
        ----------
        successor: BaseAnimationJob
            The job to start when we are done with this animation. The job's 
            .finish() function will be called.
        """
        self.successors.append(job)

    def start(self):
        self.started = True

    def finish(self):
        """
        Flag this job as finished and stop and dependents we have

        Notes
        -----
        Unless overridden, this will stop our dependents, their dependents,
        and so-on.
        """
        self.finished = True
        for job in self.dependents:
            job.finish()
        for job in self.successors:
            job.start()

class JobWithTrigger(BaseJob):
    def __init__(self, job, trigger, action, startImmediately=True):
        """
        Constructor

        Parameters
        ----------
        textColor: tuple(int, int, int, int)
            RGBA code for text color
        """
        super().__init__(startImmediately)

        self.job = job
        self.trigger = trigger
        self.action = action 

    def step(self):
        self.job.step()
        if self.trigger():
            self.action()

def DELAY_TRIGGER(delay):
    """
    Creates a predicate that when evaluated returns whether delay seconds 
    have passed since time of first evaluation.
    
    Parameters
    ----------
    delay: float 
        Time in seconds to be used in predicate returned
    """
    import time
    startTime = None
    def trigger():
        nonlocal startTime # use startTime from DELAY_TRIGGER
        # First call sets start time
        if startTime is None:
            startTime = time.time()
        return (time.time() - startTime) > delay
    return trigger

class DrawOrder(Enum):
    BEFORE = 0
    AFTER  = 1

class Topic():
    def __init__(self, priority):
        self.jobs = []
        self.priority = priority

    def register_job(self, job, drawOrder):
        match drawOrder:
            case DrawOrder.BEFORE:
                self.jobs.insert(0, job)
            case DrawOrder.AFTER:
                self.jobs.append(job)
    
    def step_jobs(self):
        jobsStepped = 0
        for job in self.jobs:
            if job.started:
                job.step()
                jobsStepped += 1
        return jobsStepped
    
    def remove_finished(self):
        self.jobs = list(filter(lambda j : not j.finished, self.jobs))
            
class JobManager():
    def __init__(self):
        self.jobLock = threading.Lock()
        self.thisFrameJobCt = 0
        self.lastFrameJobCt = 0
        self.allTopics = {} # (topic, priority) : jobList

    def create_topic(self, topic, priority = 0):
        """
        Add a topic that jobs can be registered under. Lower numbered priorities
        are stepped before higher ones.
        """
        with self.jobLock:
            self.allTopics[topic] = Topic(priority)

    def register_job(self, job, topic, drawOrder=DrawOrder.AFTER):
        """
        ## TODO AIDEN FIX PLEASE
        Register an job under a topic with some topicPiority.
        Jobs are rendered from BEFORE to AFTER priority. Any job registered
        with BEFORE priority will be drawn before all previously registered jobs
        within the topic and AFTER priority will be drawn after previously
        registered jobs in the topic. 
        """
        with self.jobLock:
            self.allTopics[topic].register_job(job, drawOrder)
            
    def step_jobs(self):
        self.lastFrameJobCt = self.thisFrameJobCt
        self.thisFrameJobCt = 0
        with self.jobLock:
            # Organize jobs in priority order
            topics = self.allTopics.values()
            topics = sorted(topics, key=lambda t : t.priority)

            for topic in topics:
                self.thisFrameJobCt += topic.step_jobs()

            self.remove_finished()

    def remove_finished(self):        
        for topic in self.allTopics.values():
            topic.remove_finished()
                
    def all_animations_stopped(self):
        """
        Becomes true only on frame when all finish
        """
        return self.lastFrameJobCt > 0 and self.thisFrameJobCt == 0