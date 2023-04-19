
import numpy as np

from .common import vbao
from .common import ConstValue

class GameMainLogic(vbao.Model):
    """
    这是用来实现游戏业务逻辑的类
    """

    def __init__(self):
        super().__init__()

        self.possible_grid_types = (0,2)


    # Game logic
    def generate(self, shape):
        x = np.random.randint(*self.possible_grid_types, shape)
        b = np.all(x != 0, axis=1)
        while np.any(b):
            idx = np.nonzero(b)[0]
            x[idx] = np.random.randint(*self.possible_grid_types, (idx.shape[0], shape[1]))
            b = np.all(x != 0, axis=1)
        return x


    def gameInit(self):
        self.combo = 0
        self.score = 0
        self.row = self.property["row"].x
        self.col = self.property["col"].x
        self.board = self.generate([self.row, self.col])

    def stepOnGrid(self, grid_no, verbose=False):
        if self.board[0, grid_no] == 0:
            self.combo += 1
        else:
            self.combo = 0
        self.updateScore()

        self.board[:-1] = self.board[1:]
        self.board[-1] = self.generate([1, self.col])

        self.calScore()
        if verbose:
            self.printScore()
        self.triggerPropertyNotifications("board")

    def updateScore(self, pure=False):
        if pure:
            return self.score

        self.score += self.combo*5


    def calScore(self):
        self.property["score"] = self.updateScore(pure=True)
        self.triggerPropertyNotifications("score")

    def printScore(self):
        print(f"score = {self.score}, combo = {self.combo}")

    def gameOver(self):
        return self.calScore()

    # For data exchanging
    def ctx(self):
        return ConstValue(self.board)