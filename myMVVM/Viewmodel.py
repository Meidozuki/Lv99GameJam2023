from .common import vbao
from .common import ConstValue

import logging


class GameViewModel(vbao.ViewModel):
    def __init__(self, row, col):
        super().__init__()
        self.listener = VMPropertyListener(self)

        self.property["row"] = ConstValue(row)
        self.property["col"] = ConstValue(col)
        self.property["score"] = 0
        self.property["playerPos"] = 0

        self.commands["prepareRender"] = ValueError("Not set yet")
        self.commands["init"] = VMInitCommand(self)
        self.commands["step"] = VMGameStepCommand(self)
        self.commands["stop"] = VMGameStopCommand(self)

    def getBoard(self):
        return self.model.ctx()

    def stepOnGrid(self, idx):
        self.property["playerPos"] = idx
        self.triggerPropertyNotifications("playerPos")
        self.model.stepOnGrid(idx)


class VMPropertyListener(vbao.PropertyListenerBase):
    def __init__(self, viewmodel_ref: GameViewModel):
        super().__init__(viewmodel_ref)

    def onPropertyChanged(self, prop_name: str):
        logging.info(f"Viewmodel receive property notif {prop_name}")
        match prop_name:
            case "board":
                self.master.runCommand("prepareRender")
            case "score":
                self.master.triggerPropertyNotifications("score")
            case "HP":
                if self.master.property["HP"] <= 0:
                    self.master.runCommand("stop")
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
        # with self._view.buffer_lock:
        self._view.buffer = self._viewmodel.getBoard().x
        self._viewmodel.triggerCommandNotifications("renderBuffer", True)


class VMCommand_with_self(vbao.CommandBase):
    def __init__(self, viewmodel_ref):
        self._viewmodel = viewmodel_ref


class VMInitCommand(VMCommand_with_self):
    def execute(self):
        self._viewmodel.model.gameInit()
        self._viewmodel.triggerCommandNotifications("init", True)


class VMGameStepCommand(VMCommand_with_self):
    def __init__(self, viewmodel_ref):
        super().__init__(viewmodel_ref)
        self.idx = None

    def setParameter(self, idx):
        self.idx = int(idx)

    def execute(self):
        if self.idx is None:
            raise ValueError("The idx is not set before step")

        self._viewmodel.stepOnGrid(self.idx)
        self._viewmodel.triggerCommandNotifications("step", True)


class VMGameStopCommand(VMCommand_with_self):
    def execute(self):
        self._viewmodel.model.gameOver()
        self._viewmodel.triggerCommandNotifications("stop", True)
