import pygame
from .GameView import View

import time
import threading
import logging
import numpy as np

class Window:
    def __init__(self):
        self.view = View()

        self.game_start = True
        self.timer_countdown = 30
        self.timer = threading.Timer(self.timer_countdown, self.interruptGame)

    # About game
    def interruptGame(self):
        self.view.runCommand("stop")
        # wait result
        # ...
        self.game_start = False

    def startLoop(self):
        start = time.time()
        while self.game_start:
            self.view.displayTime(start, self.timer_countdown)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt("Game window closed by user.")
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handleMouseClick(event.pos)

            pygame.display.flip()

    def handleMouseClick(self, click_pos):
        x, y = click_pos
        u, d, l, r = self.view.boardZone
        row, col = self.view.property.row.x, self.view.property.col.x
        grid_h, grid_w = (d - u) / row, (r - l) / col

        x = np.clip(x, l, r-1)
        idx = np.floor((x - l) / grid_w)
        self.view.commands["step"].setParameter(idx)
        self.view.runCommand("step")
