import pygame
from .common import vbao

import threading
import logging
import itertools
import numpy as np


class View(vbao.View):
    def __init__(self):
        super().__init__()
        self.cmd_listener = CommandListener(self)

        self.buffer = None
        self.buffer_lock = threading.Lock()

        self.blank_border = (200,50,100,100)

    # About display

    def initWindow(self, title="Hello World"):
        pygame.display.set_caption(title)
        self.screen = pygame.display.set_mode(size=(800, 600))

        pic = pygame.image.load(
            "local/img/craftpix-net-725990-octopus-jellyfish-shark-and-turtle-free-sprite-pixel-art/2/Idle.png")
        self.screen.blit(pic, (100, 100))

    @property
    def windowSize(self):
        """
        :return: window size (width, height)
        """
        return pygame.display.get_surface().get_size()

    @property
    def boardZone(self):
        w,h = self.windowSize
        u,d,l,r = self.blank_border
        return (u, h-d, l, w-r)

    def handleRender(self):
        with self.buffer_lock:
            data = self.buffer

        row, col = data.shape
        u,d,l,r = self.boardZone
        grid_h, grid_w = (d-u)/row, (r-l)/col
        grid_size = np.array([grid_w, grid_h])
        left_upper = np.array([l,u])
        for i, j in itertools.product(range(row), range(col)):
            pos = left_upper + grid_size * [j,i]
            self.handleGrid(data[i, j], pos, grid_size)
        pygame.display.flip()

    def handleGrid(self, grid, pos, grid_size):
        colors = {0: (0, 0, 255),
                  1: (255, 255, 255)}
        color = colors[grid]

        rect = (*pos, *grid_size)
        pygame.draw.rect(self.screen, color, rect)

class Window:
    def __init__(self):
        self.view = View()

        self.game_start = True
        self.timer = threading.Timer(30, self.interruptGame)

    # About game
    def interruptGame(self):
        self.view.runCommand("stop")
        # wait result
        # ...
        self.game_start = False

    def startLoop(self):
        while self.game_start:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt("Game window closed by user.")
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handleMouseClick(event.pos)

                pygame.display.update()

    def handleMouseClick(self, click_pos):
        x,y = click_pos
        u,d,l,r = self.view.boardZone
        row,col = self.view.property.row.x, self.view.property.col.x
        grid_h, grid_w = (d-u)/row, (r-l)/col

        x = np.clip(x,l,r)
        idx = np.floor((x-l)/grid_w)
        self.view.commands["step"].setParameter(idx)
        self.view.runCommand("step")


class CommandListener(vbao.CommandListenerBase):
    def __init__(self, view: View):
        super().__init__(view)

    def onCommandComplete(self, cmd_name: str, success: bool):
        logging.info(f"View receive command notif {cmd_name}")
        match cmd_name:
            case "init":
                if not success: raise RuntimeError
                self.master.initWindow()
            case "prepareRender":
                if not success: return
                self.master.handleRender()
            case "stop":
                if not success: return
