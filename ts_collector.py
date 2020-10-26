import math
import time
import json

class TsCollector:
    @staticmethod
    def msTS():
        return math.floor(time.time()*1000)

    
    def minUpd(self, idx, value):
        value = value - self.prev 

        if self.mins[idx] >= 0:
            if self.mins[idx] > value:
                self.mins[idx] = value
        else:
            self.mins[idx] = value


    def maxUpd(self, idx, value):
        value = value - self.prev 

        if self.maxs[idx] >= 0:
            if self.maxs[idx] < value:
                self.maxs[idx] = value
        else:
            self.maxs[idx] = value


    def avgUpd(self, idx, value):
        value = value - self.prev 

        self.avgs[idx] = (self.avgs[idx]*(self.tick[idx]-1) + value) / self.tick[idx]
        self.tick[idx] = self.tick[idx] + 1


    def __init__(self):
        self.labels = []
        self.mins = []
        self.avgs = []
        self.maxs = []
        self.tick = []

        self.prev = 0

    def start(self):
        if self.prev == 0:
            self.prev = self.msTS

    def ts(self, label):
        cts = self.msTS()

        try:
            idx = self.labels.index(label)
            self.minUpd(idx, cts)
            self.maxUpd(idx, cts)
            self.avgUpd(idx, cts)
        except Exception:
            self.labels.append(label)
            self.mins.append(-1)
            self.maxs.append(-1)
            self.avgs.append(0)
            self.tick.append(1)
            
        self.prev = self.msTS()


    def __str__(self):
        arr = []
        summa = 0
        for i in range(len(self.labels)):
            summa = summa + self.avgs[i]
            proto = {"idx": i, "label": self.labels[i], "stats": str(self.mins[i])+'/'+str(self.avgs[i])+'/'+str(self.maxs[i]), "sum": summa, "tick": self.tick[i]}
            arr.append(proto)
        
        return json.dumps(arr)

    def stats(self):
        arr = []
        summa = 0
        for i in range(len(self.labels)):
            summa = summa + self.avgs[i]
            proto = {"idx": i, "label": self.labels[i], "stats": str(self.mins[i])+'/'+str(self.avgs[i])+'/'+str(self.maxs[i]), "sum": summa, "tick": self.tick[i]}
            arr.append(proto)
        return arr