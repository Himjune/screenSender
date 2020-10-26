import math, json, base64, time
import asyncio, websockets

import threading, queue

class worker():
    def __init__(self, master):
        self.queue = queue.Queue()
        self.master = master

        self.clients = set()
        self.clients_n = 0

        self.thread = threading.Thread(target=self.process)
        
        self.thread.start()

    async def register(self, websocket):
        self.clients.add(websocket)
        self.clients_n = self.clients_n+1

    async def unregister(self, websocket):
        self.clients.remove(websocket)
        self.clients_n = self.clients_n-1

    def distribute(self, msg):
        self.queue.put_nowait(msg)

    def handle_client(self, websocket):
        await self.register(websocket)
        try:
            async for message in websocket:
                print(message)
                #data = json.loads(message)
                #can inform self.master here
        finally:
            print('disc')
            await self.unregister(websocket)

    def process(self):
        #May be shoulld start thread's loop here

        while True:
            msg = self.queue.get()
            
            if self.clients:     
                packet = json.dumps({"ts": math.floor(time.time()*1000), "ws_msg": msg})       
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
        for i in range(len(self.workers)):
            self.workers[i].distribute(msg)

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
        self.workers = [worker(self)]*5
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