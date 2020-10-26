import math, json, base64, time
import asyncio, websockets

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



    def to_clients(self, msg, tser):
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