
import numpy as np

from .common import vbao
from .common import ConstValue

class GameMainLogic(vbao.Model):
    """
    这是用来实现游戏业务逻辑的类

    """

    def __init__(self):
        super().__init__()

        self.possible_grid_types = (0,3)

    def ctx(self):
        return ConstValue(self.board)

    def gameInit(self):
        self.row = self.property["row"].x
        self.col = self.property["col"].x
        self.board = np.random.randint(*self.possible_grid_types, [self.row, self.col])


    def gameOver(self):

        return self.calScore()

    def calScore(self):
        self.property["score"] = f()
        self.triggerPropertyNotifications("score")