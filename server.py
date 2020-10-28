import math, json, base64, time

import threading
import asyncio, websockets

import http.server
import socketserver

class wsServer():
    async def register(self, websocket):
        self.client = websocket

    async def unregister(self, websocket):
        self.client = None
        self.occupied = False

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
        
        if (self.client is not None):            
            await self.client.send(packet)
            tser.ts('sent')
            return 0
        else:
            #print('NoUsers')
            return 1


    def __init__(self,port):
        self.working = True
        self.client = None
        self.occupied = False
        
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

class HttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    SERVER_CNTRL = None
    def do_GET(self):
        print('Handle', self.path)
        if self.path == '/wsc':
            # Sending an '200 OK' response
            self.send_response(200)

            # Setting the header
            self.send_header("Content-type", "text/plain")

            # Whenever using 'send_header', you also have to call 'end_headers'
            self.end_headers()

            allowed_port = '14000'
            allowed_port = self.SERVER_CNTRL.get_free_port()

            #TODO check if port available
            print('GIVEN', allowed_port)
            self.wfile.write(bytes(allowed_port, "utf8"))
            return
        else:
            self.path = 'client/'+self.path
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

class serverController():
    BASE_PORT = 14000
    http_handler = HttpRequestHandler

    def __init__(self, workers):
        self.servers = [] 
        self.thread = threading.Thread(target=self.start)

        for i in range(workers):
            self.servers.append(wsServer(self.BASE_PORT+1+i))

        self.thread.start()

    def get_free_port(self):
        idx = -1
        #TODO check if some allowed port is unused bt timestamps check
        for i in range(len(self.servers)):
            serv = self.servers[i]
            if serv.occupied == False and serv.client is None:
                serv.occupied = True
                idx = i
                break

        allowed_port = str(self.BASE_PORT + 1+ idx)
        return allowed_port

    def to_clients(self, msg, tser):
        tser.ts('go_schedule')
        for i in range(len(self.servers)):
            asyncio.run_coroutine_threadsafe(self.servers[i].update_clients(msg, tser), loop=self.servers[i].loop)
            

    def start(self):
        PORT = 8000
        self.http_handler.SERVER_CNTRL = self
        my_server = socketserver.TCPServer(("", PORT), self.http_handler)
        my_server.serve_forever()

