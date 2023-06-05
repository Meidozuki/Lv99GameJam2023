import time

import numpy as np

from .common import vbao
from .common import ConstValue
from .pawn import *


class QuadTree:
    class QuadTreeNode:
        def __init__(self, low=np.array([0., 0.]), high=np.array([1., 1.]), loose_factor=0.2):
            self.low = low
            self.high = high
            self.loosed_range = (high - low) * (1 + loose_factor) / 2
            self.nodes = None

        def isUpper(self, val, idx):
            return val >= (self.high - self.loosed_range)[idx]

        def isLower(self, val, idx):
            return val <= (self.low + self.loosed_range)[idx]

        @property
        def hasChildren(self):
            return self.nodes is not None

        def createChildren(self):
            cons = type(self)
            self.nodes = []

            lx, ly = self.low
            cx, cy = (self.low + self.high) / 2
            hx, hy = self.high

            paras = [(lx, ly), (cx, cy),
                     (lx, cy), (cx, hy),
                     (cx, ly), (hx, cy),
                     (cx, cy), (hx, hy)]
            paras = np.array(paras).reshape([4, 2, 2])

            for xy in paras:
                self.nodes.append(cons(*xy))

        def divide(self, leaves, max_num_each_node=2, max_depth=4):
            self.leaves = leaves
            nodes = [[], [], [], []]
            if len(leaves) <= max_num_each_node:
                return

            if max_depth <= 0:
                return

            self.createChildren()

            def addLeaf(x_cond, y_cond, true_fn):
                if x_cond and y_cond:
                    true_fn()

            for leaf in leaves:
                def push_leaf(idx):
                    def f():
                        nodes[idx].append(leaf)

                    return f

                x, y = leaf.position
                addLeaf(self.isLower(x, 0), self.isLower(y, 1), push_leaf(0))
                addLeaf(self.isLower(x, 0), self.isUpper(y, 1), push_leaf(1))
                addLeaf(self.isUpper(x, 0), self.isLower(y, 1), push_leaf(2))
                addLeaf(self.isUpper(x, 0), self.isUpper(y, 1), push_leaf(3))

            for i in range(4):
                self.nodes[i].divide(nodes[i], max_depth=max_depth - 1)

    def __init__(self, objects: list[Collidable]):
        self.root = QuadTree.QuadTreeNode()
        self.root.divide(objects)

    def hit(self, x, y, radius):
        # find leaf node
        node = self.find(x, y)
        center = np.array([x, y])
        re = []
        for nd in node.leaves:
            dist = np.linalg.norm(center - np.array(nd.position))
            if dist < radius:
                re.append(nd)
        return re

    def find(self, x, y):
        # find leaf node
        center = np.array([x, y])

        def go(node):
            if not node.hasChildren:
                return node
            else:
                mid = (node.low + node.high) / 2
                xphase, yphase = center > mid
                idx = xphase * 2 + yphase
                return go(node.nodes[idx])

        return go(self.root)

    def traversal(self):
        def go(node):
            if node.hasChildren:
                print("parent = ", node.low, node.high, node.leaves)
                for nd in node.nodes:
                    print(nd.leaves)
                print()
                for nd in node.nodes:
                    go(nd)

        go(self.root)


class GameMainLogic(vbao.Model):
    """
    这是用来实现游戏业务逻辑的类
    """

    def __init__(self):
        super().__init__()

        self.reset()
        self.enemies = []

    # 用来初始化，或者注销标记gc
    def reset(self):
        self.combo = 0
        self.score = 0

    # Game logic
    def initGame(self):
        self.player = Player()
        self.property["player_pos"] = self.player.position
        self.generateEnemy()

    def updateScore(self, pure=False):
        if pure:
            return self.score

        self.score += (self.combo + 1) // 2 * 5

    def calScore(self):
        self.property["score"] = int(self.updateScore(pure=True))
        self.triggerPropertyNotifications("score")

    def printScore(self):
        print(f"score = {self.score}, combo = {self.combo}")

    def gameOver(self):
        self.calScore()
        self.reset()

    def generateEnemy(self):
        self.enemies.append(Enemy())

    def collisionDetect(self):
        # 4叉树
        quadtree = QuadTree(self.enemies)
        collided = quadtree.hit(*self.player.position, self.player.collision_radius)
        return collided
