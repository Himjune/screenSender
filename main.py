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
from server import wsServer

import tornado.ioloop
import tornado.web

import hashlib

class ScreenCapturer:
    def __init__(self):
        self.buffers = [{},{}]

        self.writeTo = 0
        self.working = True
        self.buf = bytearray(1048576)
        self.data = io.BytesIO()
        self.to_send = bytes()

        self.tser = TsCollector()

    def update(self):
        while(self.working):
            self.tser.start()
            
            self.buffers[self.writeTo] = pyautogui.screenshot()
            self.tser.ts('got_img')

            data = io.BytesIO()
            self.buffers[self.writeTo].save(data, 'JPEG', quality=90)
            data.seek(0)
            self.tser.ts('got_img_to_buf')

            self.writeTo = (self.writeTo+1)%2
            
            red = data.readinto(self.buf)
            self.tser.ts('red_img_to_buf')

            data = base64.b64encode(self.buf[:red])
            data = ascii(data)
            data = data[2:-1]
            self.tser.ts('got_base64')

            self.to_send = data

            #print('got:', abs(hash(self.to_send)) % (10 ** 8))

            self.tser.ts('red_img_to_send')

            if (self.tser.tick[0] % 100 == 0):
                print(self.tser)
            
    def get_buff(self):

        return self.to_send

        #readFrom = 1-self.writeTo
        #return self.buffers[readFrom]

    def stop(self):
        self.working = False

scp = ScreenCapturer() 
class MainHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        #self.set_header("Cache-control", "no-cache")

    def get(self):
        self.set_header("Content-Type", "text/plain")
        #print(scp.get_buff())
        #print('send:', abs(hash(scp.to_send)) % (10 ** 8))
        
        self.write(scp.to_send)

    def options(self):
        # no body
        self.set_status(204)
        self.finish()

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    screenThread = threading.Thread(target=scp.update)
    screenThread.start()

    #serverThread = threading.Thread(target=server)
    #serverThread.start()

    working = True
    try:
        app = make_app()
        app.listen(8888)
        tornado.ioloop.IOLoop.current().start()

    except (KeyboardInterrupt, SystemExit):
        scp.stop()
        working = False