import pygame

import vbao
from .GameView import View
from .common import color

import time
import threading
import logging
import numpy as np


class Window:
    def __init__(self):
        self.view = View()
        self.view.upper_notify = GameOverMessage(self)

        self.game_start = True
        self.timer_countdown = 30
        self.timer = threading.Timer(self.timer_countdown, self.interruptGame)

        self.state = None

    def initGame(self):
        self.state = StateAtMenu(self)

    # About game
    def interruptGame(self):
        self.view.runCommand("stop")
        # wait result
        # ...
        self.game_start = False

    def startLoop(self):
        state = StateInGame(self)
        start = time.time()

        while self.game_start:
            self.view.displayTime(start, self.timer_countdown)
            self.view.displayPlayerStatus()
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

        x = np.clip(x, l, r - 1)
        idx = np.floor((x - l) / grid_w)
        self.view.commands["step"].setParameter(idx)
        self.view.runCommand("step")

class GameOverMessage(vbao.CommandListenerBase):
    def onCommandComplete(self, cmd_name: str, success: bool):
        logging.info(f"Window receive command notif from view {cmd_name}")
        match cmd_name:
            case "gameOver":
                self.master.game_start = False

class StateAtMenu:
    def __init__(self, window_ref):
        self.window = window_ref
        w,h = self.window.view.windowSize
        lu = w*0.4, h*0.5
        wh = w*0.2, 40
        self.start_button_zone = pygame.Rect(lu,wh)
        self.end_button_zone = pygame.Rect(lu[0], lu[1]+wh[1]+10, *wh)

    def wait(self):
        view = self.window.view
        view.clearScreen()

        self.window.view.showMainTitle(self.start_button_zone, self.end_button_zone)

        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt("Game window closed by user.")
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handleMouseClick(event.pos)



class StateInGame:
    def __init__(self, window_ref, game_time=30, max_hp: int = 3):
        self.window = window_ref
        self.game_time = game_time
        self.maxHP = max_hp
        self.HP = max_hp
        self.window.view.property["HP"] = max_hp
        self.window.view.property["maxHP"] = max_hp

    def startGame(self):
        self.window.view.displayPlayerStatus()
