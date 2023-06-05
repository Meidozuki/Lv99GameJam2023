import pygame

import vbao
from .GameView import View
from .common import color

import asyncio
import threading
import time, logging
import numpy as np


class Window:
    def __init__(self):
        self.view = View()
        self.view.upper_notify = GameOverMessage(self)

        self.state = None

    def quitGame(self):
        self.view.clearScreen()

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

    def finishState(self):
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
        lu = w * 0.3, h * 0.4
        wh = w * 0.4, 70
        self.start_button_zone = pygame.Rect(lu, wh)
        self.end_button_zone = pygame.Rect(lu[0], lu[1] + wh[1] + 20, *wh)

    async def idle(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.finishState()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handleMouseClick(event.pos)
        await asyncio.sleep(0.05)

    def wait(self):
        view = self.window.view
        view.clearScreen()

        self.window.view.showMainTitle(self.start_button_zone, self.end_button_zone)

        pygame.display.flip()
        while self.running:
            task = view.loop.create_task(self.idle())
            view.loop.run_until_complete(task)

        return self.next_state

    def handleMouseClick(self, click_pos):
        x, y = click_pos
        start = self.start_button_zone
        end = self.end_button_zone
        if start.x < x < start.x + start.width \
                and start.y < y < start.y + start.height:
            self.finishState()
            self.next_state = StateInGame
        elif end.x < x < end.x + end.width \
                and end.y < y < end.y + end.height:
            self.finishState()


class StateInGame(FSMState):
    def __init__(self, window_ref, game_time=30, max_hp: int = 3):
        super().__init__()
        self.window = window_ref
        self.game_time = game_time
        self.maxHP = max_hp
        self.window.view.property["HP"] = max_hp
        self.window.view.property["maxHP"] = max_hp

        self.timer_countdown = 10
        self.timer = threading.Timer(self.timer_countdown, self.finishState)

    def wait(self):
        view = self.window.view
        view.clearScreen()

        view.runCommand("initGame")

        view.displayScore(first=True)
        view.displayTurtle()
        view.displayPawns()

        try:
            self.timer.start()
            t = view.loop.create_task(self.startGame())
            view.loop.run_until_complete(t)
        finally:
            self.timer.cancel()
        return self.next_state

    def finishState(self):
        self.running = False
        self.next_state = StateScored

    async def startGame(self):
        view = self.window.view
        view.property.player_pos = np.array(view.windowSize) / 2
        start = time.time()

        while self.running:
            view.displayTime(start, self.timer_countdown)
            view.displayPlayerStatus()
            if view.property.HP <= 0:
                self.finishState()
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.finishState()

            await asyncio.sleep(0.05)
            pygame.display.flip()


class StateScored(FSMState):
    def __init__(self, window_ref):
        super().__init__()
        self.window = window_ref

    def wait(self):
        self.window.view.showScore()

        pygame.display.flip()
        time.sleep(0.5)  # 防止点击过头
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.MOUSEBUTTONDOWN:
                    self.finishState()

        return self.next_state
