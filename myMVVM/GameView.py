import pygame
from .common import vbao, color

import asyncio
from asyncio import CancelledError
import time, logging
import itertools
import numpy as np
from functools import wraps
from easydict import EasyDict


def scalePic(pic, factor):
    w, h = pic.get_size()
    target = (int(w * factor), int(h * factor))
    return pygame.transform.scale(pic, target)


def getPosAlignedByCenter(ref: pygame.Rect, img: pygame.Surface):
    w, h = img.get_size()
    return ref.centerx - w / 2, ref.centery - h / 2


def cancellableCoroutine(func):
    @wraps(func)
    async def inner(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except CancelledError:
            print(func.__name__, "cancelled")

    return inner


def getFont(font=None, size=12):
    if font is not None:
        assert isinstance(font, str)

    match font:
        case "arcade":
            path = "./local/font/ARCADECLASSIC.ttf"
        case None:
            path = "./local/font/x16y32pxGridGazer.ttf"
        case _:
            raise ValueError(f"cannot find font {font}")

    return pygame.font.Font(path, size)


def getTextFigure(font, text, color='0xffffff', *args):
    return font.render(text, True, color, *args)


class View(vbao.View):
    def __init__(self):
        super().__init__()
        self.prop_listener = PropertyListener(self)
        self.cmd_listener = CommandListener(self)
        self.upper_notify = None

        self.buffer = None
        self.buffer_lock = asyncio.Lock()

        self.loop = asyncio.get_event_loop()
        self.running_tasks = []

        self.screen = None
        self.blank_border = (200, 50, 20, 20)
        self.score_pos = [(500, 50), None]

        self.HP_bar_opt = EasyDict({
            'pos': np.array((100, 10)),
            'size': np.array((200, 25)),
            'blank': np.array((3, 0)),
            'color': ((200, 0, 0), (100, 0, 0)),
            'bgcolor': [192] * 3
        })
        border = np.array([4, 3])
        self.HP_bar_opt.background = pygame.Rect(self.HP_bar_opt.pos - border,
                                                 self.HP_bar_opt.size + border * 2 - self.HP_bar_opt.blank)

    # properties
    @property
    def windowSize(self):
        """
        :return: window size (width, height)
        """
        return pygame.display.get_surface().get_size()

    @property
    def playerRect(self):
        l, u, w, _ = self.boardRect
        height = 50
        return l, u - height, w, height

    # 屏幕相关
    def clearScreen(self):
        self.screen.fill(color.black)
        pygame.display.flip()

    def initWindow(self, title="Hello World"):
        pygame.display.set_caption(title)
        self.screen = pygame.display.set_mode(size=(800, 600))
        self.screen.fill('0x000000')

    # tasks相关
    def cancelTasks(self):
        for task in self.running_tasks:
            task.cancel()
            self.loop.run_until_complete(task)
        self.running_tasks.clear()

    def pushTask(self, coroutine):
        task = self.loop.create_task(coroutine)
        self.running_tasks.append(task)

    # utility
    def drawRect(self, color, rect, **args):
        pygame.draw.rect(self.screen, color, rect, **args)

    # About display
    def loadGif(self, img, pos, frames=4, interval=0.3):
        if not callable(pos):
            p = pos
            pos = lambda: p
        w, h = img.get_size()
        wi = w // frames

        for i in range(frames):
            rect = [i * wi, 0, wi, h]
            sub = img.subsurface(rect)
            self.drawAndCover(sub, pos())
            time.sleep(interval)

    async def loadGif_a(self, img, pos, frames=4, interval=0.3, endless_loop=True):
        if not callable(pos):
            p = pos
            pos = lambda: p
        w, h = img.get_size()
        wi = w // frames

        while endless_loop:
            for i in range(frames):
                rect = [i * wi, 0, wi, h]
                sub = img.subsurface(rect)
                self.drawAndCover(sub, pos())
                await asyncio.sleep(interval)

    # 显示相关
    def showMainTitle(self, start_button_zone, end_button_zone):
        self.displayTurtle()

        blue = [0, 0, 100]
        self.drawRect(blue, start_button_zone)
        self.drawRect(color.grey, start_button_zone, width=3)
        self.drawRect(blue, end_button_zone)
        self.drawRect(color.grey, end_button_zone, width=3)

        font = getFont("arcade", size=round(start_button_zone.width * 0.16))
        text = getTextFigure(font, "start game")
        self.screen.blit(text, getPosAlignedByCenter(start_button_zone, text))
        text = getTextFigure(font, "quit game")
        self.screen.blit(text, getPosAlignedByCenter(end_button_zone, text))

    def showScore(self):
        score = self.property.score
        self.drawRect('0x777777', [200, 200, 200, 200])
        font = getFont()
        text = getTextFigure(font, f'score={score}')
        self.screen.blit(text, [300, 300])

    def displayTurtle(self):
        pic = pygame.image.load("local/img/TurtleIdle.png")
        pic = scalePic(pic, 2)
        self.pushTask(self.loadGif_a(pic, (100, 70)))

    async def updatePawn(self, pawn, sleep_time=0.1):
        while True:
            # Shark会更改image，需要放在循环中
            frames, img = pawn.getImage()
            w, h = img.get_size()
            wi = w // frames

            # 播放gif每一帧
            for i in range(frames):
                # 第一时间退出循环
                if not pawn.valid:
                    return

                x, y = pawn.position
                new_pos = x * self.windowSize[0], y * self.windowSize[1]
                sub = img.subsurface([i * wi, 0, wi, h])
                self.drawAndCover(sub, new_pos)
                await asyncio.sleep(sleep_time)

                # 覆盖当前位置，避免重影
                rect = pygame.Rect(new_pos, img.get_size())
                self.screen.fill('0x000000', rect)

    def displayPawns(self):
        self.runCommand("prepareRender")

        for item in self.property.pawn:
            self.pushTask(self.updatePawn(item))

    def playJumpAnim(self):
        pic = pygame.image.load("local/img/Jump.png")
        pic = scalePic(pic, 3)
        x = int(self.screen.get_size()[0] * 0.4)
        y = 300
        self.loadGif(pic, (x, y), 6, 0.2)

    def drawAndCover(self, img, pos):
        rect = pygame.Rect(pos, img.get_size())
        self.screen.fill('0x000000', rect)
        self.screen.blit(img, pos)
        pygame.display.update(rect)

    def displayScore(self, first=False):
        font = getFont(size=30)
        if first:
            text = getTextFigure(font, "Score: ")
            pos0 = self.score_pos[0]
            self.screen.blit(text, pos0)

            width = text.get_size()[0]
            self.score_pos[1] = (pos0[0] + width, pos0[1])

        text = getTextFigure(font, str(self.property.score))
        self.drawAndCover(text, self.score_pos[1])

    def displayTime(self, start, countdown):
        font = getFont(size=20)
        time_ = time.time()
        text = getTextFigure(font, "{:.2f}".format(countdown - (time_ - start)))
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


class CommandListener(vbao.CommandListenerBase):
    def __init__(self, view: View):
        super().__init__(view)

    def onCommandComplete(self, cmd_name: str, success: bool):
        logging.info(f"View receive command notif {cmd_name}")
        match cmd_name:
            case "init":
                if not success: raise RuntimeError
                self.master.initWindow()
            case "renderBuffer":
                if not success: return
                # self.master.handleBoardRender()
            case "stop":
                if not success: return
                print("final score:", self.master.property.score)
                self.master.upper_notify.onCommandComplete("gameOver", True)
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
                # 更新score耗时少，将主线程用于更新棋盘
                self.master.displayScore()
            case "playerPos":
                pass
            case _:
                logging.warning(f"uncaught prop {prop_name}")
