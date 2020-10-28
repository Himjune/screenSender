import math, json, base64, time

import threading, queue
import asyncio, websockets

import ts_collector

class wsServer():
    async def register(self, websocket):
        self.clients.add(websocket)
        print(self.clients)

    async def unregister(self, websocket):
        self.clients.remove(websocket)

    async def handle(self, websocket, path):
        await self.register(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
        finally:
            print('disc')
            await self.unregister(websocket)

    async def update_clients(self, msg, tser):
        tser.ts('ready_to_send')

        if self.clients:   
            packet = json.dumps({"ts": math.floor(time.time()*1000), "stats": tser.stats(), "data": msg})
            tser.ts('packet_formed')   

            await asyncio.wait([client.send(packet) for client in self.clients], return_when=asyncio.FIRST_COMPLETED)
            tser.ts('sent')
            #print('\nSTATS:\n', tser, '\n***\n\n')
            return 0
        else:
            #print('NoUsers')
            return 1


    #TODO can try queues for sennnding
    async def to_clients(self, msg, tser):
        if (not self.clients): return 0

        
        tser.ts('on ws to_client')
        #asyncio.ensure_future(self.update_clients(msg), loop=self.loop)
        future = asyncio.run_coroutine_threadsafe(self.update_clients(msg, tser), loop=self.loop)
        '''try:
            result = future.result(3)
        except asyncio.TimeoutError:
            print(self.port, 'to_clients timeout')
            future.cancel()
        except Exception as exc:
            print(self.port, f'coroutine exception: {exc!r}')
        else:
            #print(f'The coroutine returned: {result!r}')
            pass
        '''


    def __init__(self,port):
        self.working = True
        self.clients = set()
        self.cnt = 0
        self.port = port

        self.loop = asyncio.new_event_loop()
        self.last_send = math.floor(time.time()*1000)

        self.thread = threading.Thread(target=self.listen)
        self.thread.start()

        

    def listen(self):
        asyncio.set_event_loop(self.loop)
        start_server = websockets.serve(self.handle, port=self.port)
        
        self.loop.run_until_complete(start_server)

        print(self.port, 'listeningg')
        self.last_send = math.floor(time.time()*1000)
        self.loop.run_forever()

class serverController():
    BASE_PORT = 14000
    def __init__(self, workers):
        self.sendQueue = queue.LifoQueue()
        self.thread = threading.Thread(target=self.process)
        self.thread.start()

        self.servers = [] 
        for i in range(workers):
            self.servers.append(wsServer(self.BASE_PORT+1+i))

    def to_clients(self, msg, tser):
        for i in range(len(self.servers)):
            asyncio.run_coroutine_threadsafe(self.servers[i].update_clients(msg, tser), loop=self.servers[i].loop)
        #self.sendQueue.put_nowait({"msg": msg, "tser": tser})

    def process(self):
        prev = ts_collector.TsCollector.msTS()
        while True:
            packet = self.sendQueue.get()
            msg = packet["msg"]
            tser = packet["tser"]

            d = ts_collector.TsCollector.msTS() - prev
            print('q', self.sendQueue.qsize(),'d:',d)
            for i in range(len(self.servers)):
                asyncio.run_coroutine_threadsafe(self.servers[i].update_clients(msg, tser), loop=self.servers[i].loop)
            prev = d