import pygame

from myMVVM import vbao
from myMVVM import GameMainLogic, GameViewModel, Window

import threading

class GameApp(vbao.App):
    def __init__(self):
        vbao.use_easydict()

        self.model = GameMainLogic()
        self.viewmodel = GameViewModel(7, 5)
        self.window = Window()

    def bind(self, *args):
        from myMVVM import VMRenderCommand

        self.viewmodel.commands.update(prepareRender=
                                       VMRenderCommand(self.viewmodel, self.window.view))
        super().bind(self.model, self.viewmodel, self.window.view, True)

    def run(self):
        pygame.init()
        self.bind()
        self.viewmodel.runCommand("init")
        self.viewmodel.runCommand("prepareRender")

        try:

            self.window.timer.start()
            self.window.startLoop()
        except KeyboardInterrupt as e:
            print(e.args)
        finally:
            self.window.timer.cancel()
            pygame.quit()

def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()