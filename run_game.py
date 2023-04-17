import pygame

from myMVVM import vbao
from myMVVM import GameMainLogic, GameViewModel, Window

import threading

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

            self.view.timer.start()
            self.view.startLoop()
        except KeyboardInterrupt as e:
            print(e.args)
        finally:
            self.view.timer.cancel()
            pygame.quit()

def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()