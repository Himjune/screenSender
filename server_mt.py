import asyncio
import json
import logging
import websockets

import math
import threading, queue

logging.basicConfig()

STATE = {"value": 0}

USERS = set()


class worker():
    def state_event(self):
        return json.dumps({"type": "state", **STATE})


    def users_event(self):
        return json.dumps({"type": "users", "count": len(USERS)})


    async def notify_state(self):
        if USERS:  # asyncio.wait doesn't accept an empty list
            message = self.state_event()
            await asyncio.wait([user.send(message) for user in USERS])


    async def notify_users(self):
        if USERS:  # asyncio.wait doesn't accept an empty list
            message = self.users_event()
            await asyncio.wait([user.send(message) for user in USERS])

            
    def __init__(self, master, name):
        self.name = name
        self.queue = queue.Queue()
        self.master = master

        self.clients = set()
        self.clients_n = 0

        self.loop = asyncio.new_event_loop()

        self.thread = threading.Thread(target=self.start)
        
        self.thread.start()

    async def register(self, websocket):
        self.clients.add(websocket)
        self.clients_n = self.clients_n+1

    async def unregister(self, websocket):
        self.clients.remove(websocket)
        self.clients_n = self.clients_n-1

    def distribute(self, msg):
        self.queue.put_nowait(msg)

    async def handle_client(self, websocket):
        print(self.name, 'got client to handle')
        # register(websocket) sends user_event() to websocket
        await self.register(websocket)
        try:
            await websocket.send(self.state_event())
            async for message in websocket:
                data = json.loads(message)
                if data["action"] == "minus":
                    STATE["value"] -= 1
                    await self.notify_state()
                elif data["action"] == "plus":
                    STATE["value"] += 1
                    await self.notify_state()
                else:
                    print("unsupported event:", data)

        finally:
            await self.unregister(websocket)

    async def process(self):
        pass

    def start(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()


class server():

    async def register(self, websocket):
        USERS.add(websocket)
        await self.notify_users()


    async def unregister(self, websocket):
        USERS.remove(websocket)
        await self.notify_users()


    def balancer(self):
        mini = 0
        minv = self.workers[0].clients_n
        for i in range(1, len(self.workers)):
            if self.workers[i].clients_n < minv:
                minv = self.workers[i].clients_n
                mini = i
        return i

    async def handle_incoming(self, websocket, path):
        print('Main got handle_incoming')

        wid = self.balancer()
        future = asyncio.run_coroutine_threadsafe(self.workers[wid].handle_client(websocket), loop=self.workers[wid].loop)
        try:
            print('try send ', self.workers[wid].name)
            result = future.result(3)
        except asyncio.TimeoutError:
            print('The coroutine took too long, cancelling the task...')
            future.cancel()
        except Exception as exc:
            print(f'The coroutine raised an exception: {exc!r}')
        else:
            #print(f'The coroutine returned: {result!r}')
            pass

        print('handle_incoming ended')

    def __init__(self):
        self.workers = [worker(self, 'uno'), worker(self, 'des'), worker(self, 'tres')]

        start_server = websockets.serve(self.handle_incoming, "localhost", 8765)

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

serv = server()
print('end script')