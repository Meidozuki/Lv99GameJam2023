import os, sys
sys.path.append(os.path.abspath("../VBAO/Lib_VBao/python"))
# sys.path.insert(0,"D:/coding/git/VBAO/Lib_VBao/python")

import vbao

class ConstValue:
    def __init__(self, value):
        self._x = value

    def getx(self):
        return self._x

    def setx(self, value):
        raise AttributeError(f"Trying to change a const value({self._x}) to {value}.")

    x = property(getx, setx)