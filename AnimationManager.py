import pygame
import threading
from enum import Enum

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
        for job in self.jobs:
            job.step()
        
        return len(self.jobs) # TODO THIS IS GROSS
    
    def remove_finished(self):
        self.jobs = list(filter(lambda j : not j.finished, self.jobs))
            
class AnimationManager():
    def __init__(self):
        self.jobLock = threading.Lock()
        self.thisFrameJobCt = 0
        self.lastFrameJobCt = 0
        self.allTopics = {} # (topic, priority) : jobList

    def create_topic(self, topic, priority = 0):
        """
        Add a topic that animations can be registered under. Lower priorities
        will be drawn first.
        """
        with self.jobLock:
            self.allTopics[topic] = Topic(priority)

    def register_job(self, job, topic, drawOrder=DrawOrder.AFTER):
        """
        ## TODO AIDEN FIX PLEASE
        Register an animation job under a topic with some topicPiority.
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
            
            for topic in topics:
                topic.remove_finished()
                
    def all_animations_stopped(self):
        """
        Becomes true only on frame when animations all finish
        """
        return self.lastFrameJobCt > 0 and self.thisFrameJobCt == 0