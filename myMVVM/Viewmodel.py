from .common import vbao
from .common import ConstValue
class GameViewModel(vbao.ViewModel):
    def __init__(self, row, col):
        super().__init__()
        self.property["row"] = ConstValue(row)
        self.property["col"] = ConstValue(col)

        self.commands["prepareRender"] = ValueError("Not set yet")
        self.commands["init"] = VMInitCommand(self)


    def getBoard(self):
        return self.model.ctx()

    def stopGame(self):
        return self.model.gameOver()

class VMInitCommand(vbao.CommandBase):
    def __init__(self, viewmodel_ref):
        self._viewmodel = viewmodel_ref

    def execute(self):
        self._viewmodel.model.gameInit()
        self._viewmodel.triggerCommandNotifications("init", True)

class VMRenderCommand(vbao.CommandBase):
    def __init__(self, viewmodel_ref, view_ref):
        self._viewmodel = viewmodel_ref
        self._view = view_ref

    def execute(self):
        with self._view.buffer_lock:
            self._view.buffer = self._viewmodel.getBoard().x
        self._viewmodel.triggerCommandNotifications("prepareRender", True)

class VMGameStopCommand(vbao.CommandBase):
    def __init__(self, viewmodel_ref):
        self._viewmodel = viewmodel_ref

    def execute(self):
        self._viewmodel.stopGame()
        self._viewmodel.triggerCommandNotifications("stop", True)