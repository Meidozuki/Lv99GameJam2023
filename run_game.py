import pygame

from myMVVM import vbao
from myMVVM import GameMainLogic, GameViewModel, Window


class GameApp(vbao.App):
    def __init__(self):

        self.model = GameMainLogic()
        self.viewmodel = GameViewModel(7, 5)
        self.view = Window()

    def bind(self, *args):
        from myMVVM import VMRenderCommand

        self.viewmodel.commands.update(prepareRender=
                                       VMRenderCommand(self.viewmodel, self.view))
        super().bind(self.model, self.viewmodel, self.view, True)

    def run(self):
        self.bind()
        self.viewmodel.runCommand("init")
        self.viewmodel.runCommand("prepareRender")

        try:
            pygame.init()

            some_flag = 1
            while some_flag:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        raise KeyboardInterrupt("Game window closed by user.")

                    pygame.display.update()
        except KeyboardInterrupt as e:
            print(e.args)
        finally:
            pygame.quit()

def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()