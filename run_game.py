import pygame
from myMVVM import App


class Window:
    def __init__(self):
        pass

    def start(self):
        pygame.init()
        screen = pygame.display.set_mode(size=(800, 600))

class GameApp(App):
    def __init__(self):
        pass

    def run(self):

        try:
            self.window.start()
            while some_flag:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        raise KeyboardInterrupt()
        finally:
            pygame.quit()

if __name__ == '__main__':
    app = GameApp()
    app.run()