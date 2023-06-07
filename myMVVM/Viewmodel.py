from .common import vbao
# from .common import ConstValue

import numpy as np
import logging
import queue


class GameViewModel(vbao.ViewModel):
    def __init__(self):
        super().__init__()
        self.listener = VMPropertyListener(self)

        self.property["score"] = 0
        self.property["pawn"] = None
        self.property["buffer"] = queue.SimpleQueue()

        self.commands["prepareRender"] = None
        self.commands["init"] = VMInitCommand(self)
        self.commands["initGame"] = VMGameInitCommand(self)
        self.commands["stopGame"] = VMGameStopCommand(self)
        self.commands["collideDetect"] = VMCollideJudgeCommand(self)
        self.commands["move"] = VMPlayerMoveCommand(self)
        self.commands["generate"] = VMGenerateCommand(self)
        self.commands["score"] = VMScoreCommand(self)

    def generateEnemy(self):
        enemy = self.model.generateEnemy()
        self.property.buffer.put(enemy)

    def initGame(self):
        self.model.initGame()
        self.property["shadow"] = False
        self.property.buffer.put(self.model.player)
        start_enemy = 5
        for i in range(start_enemy):
            self.generateEnemy()

    def judgeCollide(self):
        collided = self.model.collisionDetect()
        return len(collided) > 0

    def updateScore(self, event_type, time=None):
        assert event_type in self.model.possible_event

        self.model.updateScore(event_type,time)


class VMPropertyListener(vbao.PropertyListenerBase):
    def __init__(self, viewmodel_ref: GameViewModel):
        super().__init__(viewmodel_ref)

    def onPropertyChanged(self, prop_name: str):
        logging.info(f"Viewmodel receive property notif {prop_name}")
        match prop_name:
            case "score":
                self.master.triggerPropertyNotifications("score")
            case "HP":
                if self.master.property["HP"] <= 0:
                    self.master.runCommand("stopGame")
            case _:
                logging.warning(f"uncaught prop {prop_name}")


class VMRenderCommand(vbao.CommandBase):
    """
    用来约定Viewmodel和View之间的缓冲区
    """

    def __init__(self, viewmodel_ref, view_ref):
        self._viewmodel = viewmodel_ref
        self._view = view_ref

    def execute(self):
        pass


class VMCommand_with_self(vbao.CommandBase):
    def __init__(self, viewmodel_ref):
        self._viewmodel = viewmodel_ref


class VMInitCommand(VMCommand_with_self):
    def __init__(self, viewmodel_ref):
        super().__init__(viewmodel_ref)
        self.once_flag = True

    def execute(self):
        if self.once_flag is True:
            self._viewmodel.triggerCommandNotifications("init", True)
            self.once_flag = False
        else:
            logging.error("Initialize run twice!")


class VMGameInitCommand(VMCommand_with_self):
    def execute(self):
        self._viewmodel.initGame()
        self._viewmodel.triggerCommandNotifications("initGame", True)


class VMCollideJudgeCommand(VMCommand_with_self):
    def execute(self):
        hit = self._viewmodel.judgeCollide()
        if hit:
            self._viewmodel.property["HP"] -= 1
            self._viewmodel.model.triggerPropertyNotifications("HP")
            self._viewmodel.property["shadow"] = True
        self._viewmodel.triggerCommandNotifications("collide", hit)


class VMGameStopCommand(VMCommand_with_self):
    def execute(self):
        self._viewmodel.model.gameOver()
        self._viewmodel.triggerCommandNotifications("stop", True)

class VMPlayerMoveCommand(VMCommand_with_self):
    def execute(self):
        player = self._viewmodel.model.player
        player.position = np.array(player.position) + np.array(*self.args)
        self._viewmodel.triggerPropertyNotifications("playerPos")

class VMGenerateCommand(VMCommand_with_self):
    def execute(self):
        self._viewmodel.generateEnemy()
        self._viewmodel.triggerCommandNotifications("generate", True)


class VMScoreCommand(VMCommand_with_self):
    def setParameter(self, event_type, time=None):
        super().setParameter(event_type,time)

    def execute(self):
        if len(self.args) == 0:
            logging.warning("score command called with no args")
            return
        self._viewmodel.updateScore(*self.args)
        self.args = []