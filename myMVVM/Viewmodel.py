from .common import vbao
# from .common import ConstValue

import logging


class GameViewModel(vbao.ViewModel):
    def __init__(self, row, col):
        super().__init__()
        self.listener = VMPropertyListener(self)

        self.property["score"] = 0
        self.property["pawn"] = None

        self.commands["prepareRender"] = ValueError("Not set yet")
        self.commands["init"] = VMInitCommand(self)
        self.commands["stop"] = VMGameStopCommand(self)


    def stepOnGrid(self, idx):
        self.property["playerPos"] = idx
        self.triggerPropertyNotifications("playerPos")
        self.model.stepOnGrid(idx)

    def renderable(self):
        return self.model.enemies + [self.model.player]


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
        self._viewmodel.property.pawn = self._viewmodel.renderable()


class VMCommand_with_self(vbao.CommandBase):
    def __init__(self, viewmodel_ref):
        self._viewmodel = viewmodel_ref


class VMInitCommand(VMCommand_with_self):
    def execute(self):
        self._viewmodel.model.initGame()
        self._viewmodel.triggerCommandNotifications("init", True)


class VMGameStopCommand(VMCommand_with_self):
    def execute(self):
        self._viewmodel.model.gameOver()
        self._viewmodel.triggerCommandNotifications("stop", True)
