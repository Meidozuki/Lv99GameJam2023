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

    def quitGame(self):
        self.game_start = False
        self.view.clearScreen()

    # About game
    def interruptGame(self):
        self.view.runCommand("stop")
        # wait result
        # ...
        self.game_start = False

    def loop(self):
        state_info = StateAtMenu
        while state_info != StateClosed:
            print(state_info)
            self.state = state_info(self)
            state_info = self.state.wait()


class GameOverMessage(vbao.CommandListenerBase):
    def onCommandComplete(self, cmd_name: str, success: bool):
        logging.info(f"Window receive command notif from view {cmd_name}")
        match cmd_name:
            case "gameOver":
                self.master.game_start = False

class FSMState:
    def __init__(self):
        self.running = True
        self.next_state = None

    def stop(self):
        self.running = False
        self.next_state = StateClosed

class StateClosed(FSMState):
    def __init__(self, window_ref):
        super().__init__()


class StateAtMenu(FSMState):
    def __init__(self, window_ref):
        super().__init__()
        self.window = window_ref
        w, h = self.window.view.windowSize
        lu = w * 0.4, h * 0.5
        wh = w * 0.2, 40
        self.start_button_zone = pygame.Rect(lu, wh)
        self.end_button_zone = pygame.Rect(lu[0], lu[1] + wh[1] + 10, *wh)

    def wait(self):
        view = self.window.view
        view.clearScreen()

        self.window.view.showMainTitle(self.start_button_zone, self.end_button_zone)

        pygame.display.flip()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handleMouseClick(event.pos)

        return self.next_state

    def handleMouseClick(self, click_pos):
        x, y = click_pos
        start = self.start_button_zone
        end = self.end_button_zone
        if start.x < x < start.x + start.width \
                and start.y < y < start.y + start.height:
            self.stop()
            self.next_state = StateInGame
        elif end.x < x < end.x + end.width \
                and end.y < y < end.y + end.height:
            self.stop()


class StateInGame(FSMState):
    def __init__(self, window_ref, game_time=30, max_hp: int = 3):
        super().__init__()
        self.window = window_ref
        self.game_time = game_time
        self.maxHP = max_hp
        self.window.view.property["HP"] = max_hp
        self.window.view.property["maxHP"] = max_hp

    def wait(self):
        self.startGame()
        return self.next_state

    def startGame(self):
        view = self.window.view
        view.runCommand("prepareRender")
        start = time.time()

        while self.running:
            view.displayTime(start, self.window.timer_countdown)
            view.displayPlayerStatus()
            if view.property.HP <= 0:
                self.stop()
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handleMouseClick(event.pos)

            pygame.display.flip()


    def handleMouseClick(self, click_pos):
        view = self.window.view
        x, y = click_pos
        u, d, l, r = view.boardZone
        row, col = view.property.row.x, view.property.col.x
        grid_h, grid_w = (d - u) / row, (r - l) / col

        x = np.clip(x, l, r - 1)
        idx = np.floor((x - l) / grid_w)
        view.commands["step"].setParameter(idx)
        view.runCommand("step")