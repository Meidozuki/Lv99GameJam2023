import pygame
from .common import vbao

import threading
import itertools

class Window(vbao.View):
    def __init__(self):
        super().__init__()
        self.cmd_listener = CommandListener(self)

        self.buffer = None
        self.buffer_lock = threading.Lock()

    def initWindow(self, title="Hello World"):
        pygame.display.set_caption(title)
        self.screen = pygame.display.set_mode(size=(800, 600))

        pic = pygame.image.load("local/img/craftpix-net-725990-octopus-jellyfish-shark-and-turtle-free-sprite-pixel-art/2/Idle.png")
        self.screen.blit(pic,(100,100))


    def handleRender(self):
        with self.buffer_lock:
            data = self.buffer

        row, col = data.shape
        self.grid_size = (50,50)
        for i,j in itertools.product(range(row), range(col)):
            pos = [j*50+200, i*50 + 200]
            self.handleGrid(data[i,j], pos)
        pygame.display.flip()

    def handleGrid(self, grid, pos):
        colors = {0: (0,0,255),
                 1: (0,120,120),
                 2: (255,255,255)}
        color = colors[grid]

        rect = (*pos, *self.grid_size)
        pygame.draw.rect(self.screen, color, rect)

class CommandListener(vbao.CommandListenerBase):
    def __init__(self, view: Window):
        super().__init__(view)

    def onCommandComplete(self, cmd_name: str, success: bool):
        print(f"View receive command notif {cmd_name}")
        match cmd_name:
            case "init":
                if not success: raise RuntimeError

                self.master.initWindow()
            case "prepareRender":
                if not success: return

                self.master.handleRender()