import pygame 
import threading

class Display():
    def __init__(self, screenWidth, screenHeight, clientGame):
        if not pygame.get_init():
            pygame.init()
        pygame.display.set_caption("Spit")
        self.screen = pygame.display.set_mode((screenWidth, screenHeight))
        self.gameState = clientGame
        self.run_thread = threading.thread(target=self.run)
        self.run_thread.start()

    def run(self):
        while True:
            pass

