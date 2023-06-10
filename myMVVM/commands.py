from .common import vbao

import numpy as np
import logging

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
        self._viewmodel.triggerCommandNotifications("collide", True)


class VMGameStopCommand(VMCommand_with_self):
    def execute(self):
        self._viewmodel.model.gameOver()
        self._viewmodel.triggerCommandNotifications("stop", True)

class VMPlayerMoveCommand(VMCommand_with_self):
    def execute(self):
        model = self._viewmodel.model
        model.setPlayerPos(np.array(model.player.position) + np.array(*self.args))

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