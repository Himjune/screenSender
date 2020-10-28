import logging
import threading
import time, math

import pyautogui

import asyncio
import json
import websockets

import io
import base64

import mss
from PIL import Image
import PIL.ImageGrab

from ts_collector import TsCollector
from server import wsServer, serverController

class ScreenCapturer:
    def __init__(self):
        self.buffers = [{},{}]

        self.writeTo = 0
        self.working = True
        self.buf = bytearray(1048576)

        self.tser = TsCollector()

    def update(self, sender):
        while(self.working):
            self.tser.start()
            self.buffers[self.writeTo] = pyautogui.screenshot()
            self.tser.ts('got_img')

            data = io.BytesIO()
            self.buffers[self.writeTo].save(data, 'JPEG', quality=70)
            data.seek(0)
            self.tser.ts('got_img_to_buf')

            self.writeTo = (self.writeTo+1)%2
            
            red = data.readinto(self.buf)
            self.tser.ts('red_img_to_buf')

            data = base64.b64encode(self.buf[:red])
            data = ascii(data)
            data = data[2:-1]
            self.tser.ts('got_base64')

            #print(self.tser.stats())
            sender.to_clients(data, self.tser)
            
    def get_buff(self):
        readFrom = 1-self.writeTo
        return self.buffers[readFrom]

    def stop(self):
        self.working = False

if __name__ == "__main__":
    scp = ScreenCapturer()
    server = serverController(3)

    screenThread = threading.Thread(target=scp.update, args=(server,))
    screenThread.start()

    working = True
    try:
        while (working):
            #print('avg',scp.avg,'\tn',scp.idx, '\twt:', scp.writeTo, end='\r')
            #server.to_clients(f'Tick {scp.idx} with avg \t{scp.avg}', 0)
            time.sleep(5)

    except (KeyboardInterrupt, SystemExit):
        scp.stop()
        working = False