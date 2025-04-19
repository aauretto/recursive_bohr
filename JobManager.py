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

        Parameters
        ----------
        startImmediately: bool
            Whether the flip should start immediately or will need to be
            triggered by another job

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
        """
        Sets the started state to be True
        """
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
    """
    Bundles together a job and some predicate. Will call action() when predicate
    returns true.
    """
    def __init__(self, job, trigger, action, startImmediately=True, triggerOnce=False):
        """
        Constructor

        Parameters
        ----------
        job: BaseJob
            The job to step when this job is stepped
        trigger: func() -> bool
            Predicate that returns true when some condition is met. Used to
            determine when / if to call action.
        action: func() -> any
            Function to be called when trigger returns true
        startImmediately: bool
            Whether this job should start on first step after being registered
        triggerOnce: bool
            Whether to call action once and once only when the first call to
            trigger returns True. If set to false, every time trigger returns
            true, action will be called.
        """
        super().__init__(startImmediately)

        self.job = job
        self.trigger = trigger
        self.action = action 
        self.triggerOnce = triggerOnce
        self.triggered = False

    def step(self):
        """
        Steps the job we own then calls action if we trigger on this step.
        
        Returns
        -------
        None
        """
        self.job.step()
        if self.trigger() and not (self.triggered and self.triggerOnce):
            self.action()
            self.triggered = True

def DELAY_TRIGGER(delay): #TODO why caps
    """
    Creates a predicate that when evaluated returns whether delay seconds 
    have passed since time of first evaluation.
    
    Parameters
    ----------
    delay: float 
        Time in seconds to be used in predicate returned
    
    Returns
    -------
    : func() -> bool
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

class TopicOrder(Enum):
    """
    Enum defining whether to add to the front or back of a topic's list of jobs.
    BEFORE = Job will be stepped before other jobs in the list
    AFTER  = Job will be stepped after other jobs in the list
    """
    BEFORE = 0
    AFTER  = 1

class Topic():
    """
    Container for a list of jobs. Can be stepped which will step all jobs in the
    topic.
    """
    def __init__(self, priority):
        """
        Constructor

        Parameters
        ----------
        priority: int
            Integer value representing the priority of this topic relative to
            other topics. Lower number = higher priority
        """
        self.jobs = []
        self.priority = priority

    def register_job(self, job, order):
        """
        Adds a job to this topic's job list.

        Parameters
        ----------
        job: BaseJob
            A job object to step when this topic is stepped.
        order: TopicOrder
            Enum value representing where to put job in this topic's job list.
    
        Returns
        -------
        None
        """
        match order:
            case TopicOrder.BEFORE:
                self.jobs.insert(0, job)
            case TopicOrder.AFTER:
                self.jobs.append(job)
    
    def step_jobs(self):
        """
        Advances all started jobs in this topic by one step.

        Returns
        -------
        jobsStepped: int
            The number of jobs we called step on
        """
        jobsStepped = 0
        for job in self.jobs:
            if job.started:
                job.step()
                jobsStepped += 1
        return jobsStepped
    
    def remove_finished(self):
        """
        Clears out all finished jobs from this topic.

        Returns
        -------
        None
        """
        self.jobs = list(filter(lambda j : not j.finished, self.jobs))
            
class JobManager():
    """
    Container for multiple topics of jobs. Allows for interleaving of BaseJob
    objects.
    """
    def __init__(self):
        """
        Constructor
        """
        # Lock that protects the job/topic lists in this manager
        self.jobLock = threading.Lock()
        self.allTopics = {} # (topic, priority) : jobList
        
        # Used to determine if we went from nonzero to zero jobs stepped 
        # when step_jobs is called
        self.thisFrameJobCt = 0
        self.lastFrameJobCt = 0

    def create_topic(self, topic, priority = 0):
        """
        Add a topic that jobs can be registered under. Lower numbered priorities
        are stepped before higher ones.

        Parameters
        ----------
        topic: any
            Hashable 
        """
        with self.jobLock:
            self.allTopics[topic] = Topic(priority)

    def register_job(self, job, topic, drawOrder=TopicOrder.AFTER):
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