import os, sys

# assert os.path.exists("./VBAO/Lib_VBao/python")
sys.path.append(os.path.abspath("./VBAO/Lib_VBao/python"))

import pygame

from myMVVM import vbao
from myMVVM import GameMainLogic, GameViewModel, Window

import time
import logging


# logging.basicConfig(level=logging.INFO)

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

        try:
            self.window.loop()
        except:
            raise
        finally:
            pygame.quit()

def main():
    app = GameApp()
    app.run()


if __name__ == '__main__':
    main()
