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

import math, json, base64, time
import asyncio, websockets

import threading, queue

class worker():
    def __init__(self, master, name):
        self.name = name
        self.queue = queue.Queue()
        self.master = master

        self.clients = set()
        self.clients_n = 0
        
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start)
        self.thread.start()
    
    def start(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.process())
        self.loop.run_forever()

    async def register(self, websocket):
        self.clients.add(websocket)
        self.clients_n = self.clients_n+1

    async def unregister(self, websocket):
        self.clients.remove(websocket)
        self.clients_n = self.clients_n-1

    async def distribute(self, msg):
        print(self.name, 'dis msg:')
        if self.clients:
            await asyncio.wait(self.queue.put(msg), return_when=asyncio.FIRST_COMPLETED)
            

    async def handle_client(self, websocket):
        await self.register(websocket)
        try:
            async for message in websocket:
                print(message)
                #data = json.loads(message)
                #can inform self.master here
        finally:
            print('disc')
            await self.unregister(websocket)

    async def process(self):
        #May be shoulld start thread's loop here

        msg = self.queue.get()
        
        if self.clients:     
            packet = json.dumps({"ts": math.floor(time.time()*1000), "ws_msg": msg})       
            print('packet ready to send')
            await asyncio.wait([client.send(packet) for client in self.clients], return_when=asyncio.FIRST_COMPLETED)

        self.queue.task_done()


class wsServer():
    async def handle(self, websocket, path):
        mini = 0
        minc = self.workers[0].clients_n

        for i in range(1, len(self.workers)):
            if minc > self.workers[i].clients_n:
                mini = i
                minc = self.workers[i].clients_n

        self.workers[mini].handle_client(websocket)


    async def update_clients(self, msg, tser):
        tser.ts('ready_to_send')

        packet = json.dumps({"ts": math.floor(time.time()*1000), "stats": tser.stats(), "data": msg})
        tser.ts('packet_formed')

        if self.clients:            
            await asyncio.wait([client.send(packet) for client in self.clients], return_when=asyncio.FIRST_COMPLETED)
            tser.ts('sent')
            #print('\nSTATS:\n', tser, '\n***\n\n')
            return 0
        else:
            #print('NoUsers')
            return 1


    def to_clients(self, data, tser):
        msg = {"stats": tser, 'data': data}
        print('to_clients')
        for i in range(len(self.workers)):
            future = asyncio.run_coroutine_threadsafe(self.workers[i].distribute(msg), loop=self.workers[i].loop)
            try:
                result = future.result(3)
            except asyncio.TimeoutError:
                print('The coroutine took too long, cancelling the task...', self.workers[i].name)
                future.cancel()
            except Exception as exc:
                print(f'The coroutine raised an exception: {exc!r}')
            else:
                #print(f'The coroutine returned: {result!r}')
                pass

        tser.ts('scheduled_sending')

    def to_clients_old(self, msg, tser):
        #asyncio.ensure_future(self.update_clients(msg), loop=self.loop)
        future = asyncio.run_coroutine_threadsafe(self.update_clients(msg, tser), loop=self.loop)
        try:
            result = future.result(3)
        except asyncio.TimeoutError:
            print('The coroutine took too long, cancelling the task...')
            future.cancel()
        except Exception as exc:
            print(f'The coroutine raised an exception: {exc!r}')
        else:
            #print(f'The coroutine returned: {result!r}')
            pass


    def __init__(self):
        self.workers = [worker(self,'uno'),worker(self,'dos'),worker(self,'tres')]
        self.working = True
        self.clients = set()
        self.cnt = 0
        self.loop = asyncio.new_event_loop()
        self.last_send = math.floor(time.time()*1000)

    def listen(self):
        asyncio.set_event_loop(self.loop)
        start_server = websockets.serve(self.handle, port=8765)
        
        self.loop.run_until_complete(start_server)
        self.loop.run_forever()


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
            img = {}
            #self.buffers[self.writeTo] = pyautogui.screenshot()
            #img = pyautogui.screenshot()
            img = PIL.ImageGrab.grab()
            '''with mss.mss() as sct:
                # Get rid of the first, as it represents the "All in One" monitor:
                for num, monitor in enumerate(sct.monitors[1:], 1):
                    # Get raw pixels from the screen
                    sct_img = sct.grab(monitor)

                    # Create the Image
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")'''
            self.tser.ts('got_img')

            data = io.BytesIO()
            #self.buffers[self.writeTo].save(data, 'JPEG', quality=70)
            img.save(data, 'JPEG', quality=10)
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
    print('a')
    scp = ScreenCapturer()
    server = wsServer()

    print('e')
    screenThread = threading.Thread(target=scp.update, args=(server,))
    screenThread.start()

    serverThread = threading.Thread(target=server.listen)
    serverThread.start()

    working = True
    try:
        while (working):
            #print('avg',scp.avg,'\tn',scp.idx, '\twt:', scp.writeTo, end='\r')
            #server.to_clients(f'Tick {scp.idx} with avg \t{scp.avg}', 0)
            time.sleep(5)

    except (KeyboardInterrupt, SystemExit):
        scp.stop()
        working = False