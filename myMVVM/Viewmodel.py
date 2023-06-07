from .common import vbao
from .common import game_setting

import queue
from .commands import *


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
        for i in range(game_setting["initEnemyNum"]):
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
            case "score" | "playerPos":
                self.master.triggerPropertyNotifications(prop_name)
            case "HP":
                if self.master.property["HP"] <= 0:
                    self.master.runCommand("stopGame")
            case _:
                logging.warning(f"uncaught prop {prop_name}")

