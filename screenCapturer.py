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