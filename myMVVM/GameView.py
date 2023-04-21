import pygame
from .common import vbao

import time
import threading
import logging
import itertools
import numpy as np
from functools import wraps
from easydict import EasyDict

class LoopThread:
    @wraps(threading.Thread.__init__)
    def __init__(self, target, args=None, **kwargs):
        if args is None:
            args = []

        def f():
            while self.running:
                target(*args,**kwargs)

        self.thread = threading.Thread(target=f)
        self.running = True

    def start(self):
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()


class View(vbao.View):
    def __init__(self):
        super().__init__()
        self.prop_listener = PropertyListener(self)
        self.cmd_listener = CommandListener(self)

        self.buffer = None
        self.buffer_lock = threading.Lock()

        self.running_threads=[]

        self.blank_border = (200, 50, 100, 50)
        self.score_pos = [(500, 50), None]

        self.HP_bar_opt = EasyDict({
            'pos': np.array((100, 10)),
            'size': np.array((200, 25)),
            'blank': np.array((3,0)),
            'color': ((200, 0, 0), (100, 0, 0)),
            'bgcolor': [192]*3
        })
        border = np.array([4,3])
        self.HP_bar_opt.background = pygame.Rect(self.HP_bar_opt.pos - border,
                                                 self.HP_bar_opt.size + border*2 - self.HP_bar_opt.blank)

    @property
    def windowSize(self):
        """
        :return: window size (width, height)
        """
        return pygame.display.get_surface().get_size()

    @property
    def boardZone(self):
        """
        :return: area box for board (up, down, left,right)
        """
        w, h = self.windowSize
        u, d, l, r = self.blank_border
        return (u, h - d, l, w - r)

    # About display
    def loadGif(self, img, pos, frames=4, interval=0.3):
        w,h = img.get_size()
        wi = w//frames

        for i in range(frames):
            rect=[i*wi,0,wi,h]
            sub = img.subsurface(rect)
            self.screen.blit(sub,pos)
            start = time.time()
            while time.time() - start < interval:
                pass

    def initWindow(self, title="Hello World"):
        pygame.display.set_caption(title)
        self.screen = pygame.display.set_mode(size=(800, 600))

        self.displayScore(True)

        pic = pygame.image.load(
            "local/img/Idle.png")
        w,h = pic.get_size()
        pic = pygame.transform.scale(pic,[w*2,h*2])
        thread = LoopThread(target=self.loadGif,args=[pic,(100, 100)])
        thread.start()
        self.running_threads.append(thread)

    def getFont(self, size=12):
        return pygame.font.Font("./local/font/x16y32pxGridGazer.ttf", size)

    def getTextFigure(self, font, text, color='0xffffff', *args):
        return font.render(text, True, color, *args)

    def drawAndCover(self, img, pos):
        rect = pygame.Rect(pos, img.get_size())
        self.screen.fill('0x000000', rect)
        self.screen.blit(img, pos)
        pygame.display.update(rect)

    def displayScore(self, first=False):
        font = self.getFont(30)
        if first:
            text = self.getTextFigure(font, "Score: ")
            pos0 = self.score_pos[0]
            self.screen.blit(text, pos0)

            width = text.get_size()[0]
            self.score_pos[1] = (pos0[0] + width, pos0[1])

        text = self.getTextFigure(font, str(self.property.score))
        self.drawAndCover(text, self.score_pos[1])

    def displayTime(self, start, countdown):
        font = self.getFont(20)
        time_ = time.time()
        text = self.getTextFigure(font, "{:.2f}".format(countdown - (time_ - start)))
        self.drawAndCover(text, (200, 50))

    def displayPlayerStatus(self):
        cur, maxHP = self.property.HP, self.property.maxHP
        HP_pos = self.HP_bar_opt.pos
        remain_color, lost_color = self.HP_bar_opt.color
        bar_width, height = self.HP_bar_opt.size
        grid_width = bar_width / maxHP
        grid_wh = np.array([grid_width, height]) - self.HP_bar_opt.blank

        pygame.draw.rect(self.screen, self.HP_bar_opt.bgcolor, self.HP_bar_opt.background)
        for i in range(maxHP):
            color = np.where(i < cur, remain_color, lost_color)
            pos = HP_pos + np.array([grid_width, 0]) * i
            pygame.draw.rect(self.screen, color, [pos, grid_wh])

        MP_pos = (100, 60)

    def handleRender(self):
        with self.buffer_lock:
            data = self.buffer

        row, col = data.shape
        u, d, l, r = self.boardZone
        grid_h, grid_w = (d - u) / row, (r - l) / col
        grid_size = np.array([grid_w, grid_h])
        left_upper = np.array([l, u])

        for i, j in itertools.product(range(row), range(col)):
            pos = left_upper + grid_size * [j, i]
            self.handleGrid(data[i, j], pos, grid_size)

        # 划分泳道：在前4条泳道的右边缘，绘制分割线
        border_h, border_w = (d - u), 5 # 分割线矩形的高宽
        border_size = np.array([border_w, border_h]) # 分割线矩形的尺寸
        border_color = (255, 0, 0) # 分割线的颜色
        for i in range(1, 5):
            delta_x = grid_w * i # 横坐标偏移量
            pos = left_upper + [delta_x, 0]
            border_rect = (*pos, *border_size)
            pygame.draw.rect(self.screen, border_color, border_rect)

        pygame.display.flip()

    def handleGrid(self, grid, pos, grid_size):
        colors = {0: (0, 0, 255),
                  1: (255, 255, 255)}
        color = colors[grid]

        rect = (*pos, *grid_size)
        pygame.draw.rect(self.screen, color, rect)


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
            case "step":
                pass
            case _:
                logging.warning(f"uncaught cmd {cmd_name}")


class PropertyListener(vbao.PropertyListenerBase):
    def __init__(self, view: View):
        super().__init__(view)

    def onPropertyChanged(self, prop_name: str):
        logging.info(f"View receive property notif {prop_name}")
        match prop_name:
            case "score":
                self.master.displayScore()
            case _:
                logging.warning(f"uncaught prop {prop_name}")
