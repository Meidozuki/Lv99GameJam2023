import asyncio

import numpy as np
import pygame
import time
import abc

from .GameView import scalePic


class Collidable:
    def __init__(self):
        super().__init__()
        self.position = (0, 0)
        # 以棋盘为(0,1)
        self.collision_radius = 0.02


class Actor(abc.ABC):
    def __init__(self):
        super().__init__()
        self.valid = True
        self.renderSetting()

    @abc.abstractmethod
    def renderSetting(self):
        self.img_path = None
        self.frames = None
        self.scale = 1

    def getImage(self):
        img = pygame.image.load(self.img_path)
        if self.scale != 1:
            img = scalePic(img, self.scale)
        return (self.frames, img)


class Player(Collidable, Actor):
    def __init__(self):
        super().__init__()
        self.position = (0.5, 0.5)

    def renderSetting(self):
        super().renderSetting()
        self.img_path = "local/img/Swim.png"
        self.frames = 6

    async def tickLogic(self, interval, pos_fn):
        pass

    def __str__(self):
        return f"Player {self.position}"


class Enemy(Collidable, Actor):
    def __init__(self):
        self.lock = False
        super().__init__()
        self.init()
        self.velocity = None
        self.route_x0 = None
        self.route_t0 = None
        self.velocity_factor = 0.15
        self.tick_interval = 0.05

    def init(self):
        d = {0: ((0, 0.1), (0, 1)),
             1: ((0.9, 1), (0, 1)),
             2: ((0, 1), (0, 0.1))
             }
        xrange, yrange = d[np.random.randint(3)]

        def random(range_):
            low, high = range_
            return np.random.randint(int(low * 20), int(high * 20)) / 20

        x, y = random(xrange), random(yrange)
        x, y = np.clip(x, 0.01, 0.99), np.clip(y, 0.01, 0.99)
        self.position = np.array([x, y])

        self.wait_seconds = np.random.randint(1, 4)

    async def tickLogic(self, pos_fn, interval=None):
        await asyncio.sleep(self.wait_seconds)
        self.lockOn(pos_fn())
        if interval is None:
            interval = self.tick_interval
        while self.valid:
            self.update()
            await asyncio.sleep(interval)

    def lockOn(self, target):
        assert not self.hitBorder(target, 0)
        self.route_x0 = np.array(self.position)
        self.velocity = (np.array(target) - self.route_x0) * self.velocity_factor
        self.route_t0 = time.time()
        self.lock = True

    def update(self):
        t = time.time()
        self.position = self.route_x0 + self.velocity * (t - self.route_t0)

    def hitBorder(self, position=None, hit_width=None):
        hit_width = self.collision_radius if hit_width is None else hit_width
        x, y = self.position if position is None else position

        if x < hit_width or x > 1 - hit_width or \
                y < hit_width or y > 1 - hit_width:
            return True
        else:
            return False

    def renderSetting(self):
        super().renderSetting()
        if self.lock is False:
            self.img_path = "local/img/SharkIdle.png"
        else:
            self.img_path = "local/img/SharkWalk.png"
        self.frames = 4

    def __str__(self):
        return f"Enemy {self.position}"
