import pygame
from myMVVM import App


class Window:
    def __init__(self):
        pass

    def start(self, title="Hello World"):
        pygame.init()
        pygame.display.set_caption(title)
        screen = pygame.display.set_mode(size=(800, 600))

        pic = pygame.image.load("local/img/craftpix-net-725990-octopus-jellyfish-shark-and-turtle-free-sprite-pixel-art/2/Idle.png")
        screen.blit(pic,(100,100))

class GameApp(App):
    def __init__(self):
        self.window = Window()

    def run(self):

        try:
            self.window.start()

            some_flag=1
            while some_flag:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        raise KeyboardInterrupt("Game window closed by user.")

                    pygame.display.update()
        except KeyboardInterrupt as e:
            print(e.args)
        finally:
            pygame.quit()

if __name__ == '__main__':
    app = GameApp()
    app.run()