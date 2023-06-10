import pygame

from .common import vbao, color, res
from .common import scalePic
from . import Enemy

import asyncio
import time, logging
import numpy as np
from functools import wraps
from easydict import EasyDict
from asyncio import CancelledError


def getPosAlignedByCenter(ref: pygame.Rect, img: pygame.Surface):
    w, h = img.get_size()
    return ref.centerx - w / 2, ref.centery - h / 2


def cancellableCoroutine(func):
    @wraps(func)
    async def inner(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except CancelledError:
            logging.info(func.__name__, "cancelled")

    return inner


async def cancellableCoroutine_AfterBuild(func):
    try:
        await func
    except CancelledError:
        print(func.__name__, "cancelled")


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

    return pygame.font.Font(res(path), size)


def getTextFigure(font, text, color='0xffffff', *args):
    return font.render(text, True, color, *args)


class View(vbao.View):
    def __init__(self):
        super().__init__()
        self.prop_listener = PropertyListener(self)
        self.cmd_listener = CommandListener(self)

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

    # 屏幕相关
    def clearScreen(self):
        self.screen.fill(color.black)
        pygame.display.flip()

    def initWindow(self, title="Hello World"):
        pygame.display.set_caption(title)
        self.screen = pygame.display.set_mode(size=(800, 600))
        self.clearScreen()

    # tasks相关
    def cancelTasks(self):
        for task in self.running_tasks:
            logging.info("canceling", task._coro.__name__, end=' ')
            task.cancel()
            self.loop.run_until_complete(task)
        self.running_tasks.clear()

    def pushTask(self, coroutine):
        task = self.loop.create_task(coroutine)
        self.running_tasks.append(task)

    # utility
    def drawRect(self, color, rect, **args):
        pygame.draw.rect(self.screen, color, rect, **args)

    def drawAndCover(self, img, pos, update_rect: tuple = ()):
        if not isinstance(update_rect, tuple):
            logging.error(update_rect,"is not a tuple")
        rect = pygame.Rect(pos, img.get_size())
        self.screen.fill('0x000000', rect)
        self.screen.blit(img, pos)
        pygame.display.update((rect,) + update_rect)

    # About display
    @cancellableCoroutine
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
        def drawBadge():
            img = pygame.image.load(res("local/img/BADGE_01.png"))
            img = scalePic(img, 0.2)
            margin = 20
            y = self.windowSize[1] - img.get_size()[1] - margin
            self.drawAndCover(img, (margin, y))

        drawBadge()
        self.displayTurtle(6)

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

    def showFinalScore(self):
        score = self.property.score
        self.drawRect('0x777777', [100, 200, 600, 200])
        font = getFont(size=20)
        text = getTextFigure(font, f'Your score={score}')
        self.screen.blit(text, [300, 300])

    def displayTurtle(self, n=1):
        pic = pygame.image.load(res("local/img/TurtleIdle.png"))
        pic = scalePic(pic, 2)
        for i in range(1, n + 1):
            self.pushTask(self.loadGif_a(pic, (i * 100, 60)))

    @cancellableCoroutine
    async def updatePawn(self, pawn, sleep_time=0.1):
        def resizePos(x, y):
            nx = x * self.windowSize[0]
            ny = (0.2 + y * 0.8) * self.windowSize[1]
            return nx, ny

        prev_rect = None
        while pawn.valid:
            # Shark会更改image，需要放在循环中
            frames, img = pawn.getImage()
            w, h = img.get_size()
            wi = w // frames

            # 播放gif每一帧
            for i in range(frames):
                # 第一时间退出循环
                if not pawn.valid:
                    break

                x, y = pawn.position
                new_pos = resizePos(x, y)
                sub = img.subsurface([i * wi, 0, wi, h])
                self.drawAndCover(sub, new_pos, update_rect=(prev_rect,))
                await asyncio.sleep(sleep_time)

                # 覆盖当前位置，避免重影
                prev_rect = pygame.Rect(new_pos, (wi, h))
                self.screen.fill('0x000000', prev_rect)

        # 摧毁时活动
        if isinstance(pawn, Enemy):
            cmd = self.commands["score"]
            cmd.setParameter("combo")
            cmd.execute()

    def displayPawns(self):
        if not self.property.buffer.empty():
            queue = self.property.buffer

            def get_pos():
                return self.property.player_pos

            @cancellableCoroutine
            async def tickLogicWrapper(pawn):
                await pawn.tickLogic(get_pos, 0.1)

            while not queue.empty():
                pawn = queue.get()
                self.pushTask(self.updatePawn(pawn))
                self.pushTask(tickLogicWrapper(pawn))

    def playJumpAnim(self):
        pic = pygame.image.load("local/img/Jump.png")
        pic = scalePic(pic, 3)
        x = int(self.screen.get_size()[0] * 0.4)
        y = 300
        self.loadGif(pic, (x, y), 6, 0.2)

    def handleKeyboardInput(self, key):
        move_val = np.array([0., 0.])
        move_dist = 0.05
        match key:
            case 'w':
                move_val[1] -= move_dist
            case 's':
                move_val[1] += move_dist
            case 'a':
                move_val[0] -= move_dist
            case 'd':
                move_val[0] += move_dist

        self.commands["move"].setParameter(move_val)
        self.runCommand("move")

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

    def displayTime(self, start):
        font = getFont(size=20)
        time_ = time.time()
        text = getTextFigure(font, "Survived {:.2f}s".format(time_ - start))
        self.drawAndCover(text, (120, 50))

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
            case "stop":
                if not success: return
                print("final score:", self.master.property.score)
            case "initGame" | "collide":
                pass
            case "generate":
                self.master.displayPawns()
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
            case "playerPos":
                pass
            case _:
                logging.warning(f"uncaught prop {prop_name}")
