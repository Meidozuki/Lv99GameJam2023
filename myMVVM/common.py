import vbao

import pygame
import numpy as np
from easydict import EasyDict


def scalePic(pic, factor):
    w, h = pic.get_size()
    target = (int(w * factor), int(h * factor))
    return pygame.transform.scale(pic, target)


def truncatedNormal(low, high, sigma=1.0, center=None):
    center = (low + high) / 2 if center is None else center
    x = np.random.normal(center, sigma)
    return np.clip(x, low, high)


class ConstValue:
    def __init__(self, value):
        self._x = value

    def getx(self):
        return self._x

    def setx(self, value):
        raise AttributeError(f"Trying to change a const value({self._x}) to {value}.")

    x = property(getx, setx)


color = EasyDict({
    'grey': '0xC0C0C0',
    'white': '0xFFFFFF',
    'black': '0x000000'
})

# 游戏设置项
game_setting = {
    "growScoreEverySeconds": 0.5,
    "growScoreAmount": 1,
    "initEnemyNum": 5,
    "invincible_time": 1
}


# 统计使用的资源
resource = set()


def res(filepath: str):
    resource.add(filepath)
    return filepath
