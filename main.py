import math
from enum import Enum
from pythonosc import dispatcher
from pythonosc import osc_server
import pyautogui

SMOOTHTIME = 10
CALIBRATE = 8
SPEED = 50
EPS = 0.001
MAX = 1

def getWiiMoteNum(path):
    return int(path[-1:])

class Mouse:
    def move(self, x, y):
        currentX, currentY = pyautogui.position()
        x = currentX + x
        y = currentY + y
        print(x, y)
        if (pyautogui.onScreen(x, y)):
            pyautogui.moveTo(x, y)

class Smoother:
    avgCenter = [0.5, 0.5]
    avgX = []
    avgY = []

    def __init__(self, smoothTime):
        for i in range(smoothTime):
            self.avgX.append(0.5)
            self.avgY.append(0.5)

    def getX(self):
        return sum(self.avgX)/len(self.avgX) - self.avgCenter[0]

    def getY(self):
        return self.avgCenter[1] - sum(self.avgY)/len(self.avgY)

    def pushX(self, v):
        if (math.fabs(v - self.avgCenter[0]) < EPS or MAX < math.fabs(v - self.avgCenter[0])):
            return self.getX()
        self.avgX.pop(0)
        self.avgX.append(v)
        return self.getX()

    def pushY(self, v):
        if (math.fabs(v - self.avgCenter[1]) < EPS or MAX < math.fabs(v - self.avgCenter[1])):
            return self.getY()
        self.avgY.pop(0)
        self.avgY.append(v)
        return self.getY()

    def updateAvg(self, x, y):
        if (x):
            self.avgCenter[0] = (x + self.avgCenter[0]) / 2
        if (y):
            self.avgCenter[1] = (y + self.avgCenter[1]) / 2
        pass

class Balance:
    calibrate = 0
    x = 0
    y = 0
    smoother = Smoother(SMOOTHTIME)
    mouse = Mouse()
    def onReceive(self, path, data):
        if (self.calibrate < CALIBRATE and 
            (getWiiMoteNum(path) == WiiMote.VIRTUAL_X.value or getWiiMoteNum(path) == WiiMote.VIRTUAL_Y.value)):
            self.calibration(path, data)
            self.calibrate += 1
            return
        if (getWiiMoteNum(path) == WiiMote.VIRTUAL_X.value or getWiiMoteNum(path) == WiiMote.VIRTUAL_Y.value):
            self.calc(path, data)

    def calibration(self, path, data):
        if (getWiiMoteNum(path) == WiiMote.VIRTUAL_X.value):
            self.smoother.updateAvg(data, None)
        if (getWiiMoteNum(path) == WiiMote.VIRTUAL_Y.value):
            self.smoother.updateAvg(None, data)

    def calc(self, path, data):
        if (getWiiMoteNum(path) == WiiMote.VIRTUAL_X.value):
            self.x = self.smoother.pushX(data)
        if (getWiiMoteNum(path) == WiiMote.VIRTUAL_Y.value):
            self.y = self.smoother.pushY(data)
        self.mouse.move(self.x * SPEED, self.y * SPEED)

class WiiMote(Enum):
    VIRTUAL_X       = 5
    VIRTUAL_Y       = 6

if __name__ == "__main__":
    balance = Balance()
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/wii/1/balance/*", balance.onReceive)

    server = osc_server.ThreadingOSCUDPServer(
        ("127.0.0.1", 8001), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()
