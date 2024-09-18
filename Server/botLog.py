#!/usr/bin/env python3
import logging, datetime
from time import gmtime, strftime

class BotLog():
    def __init__(self):
        # print("BOT LOG INIT")
        self.init = False
        self.count = 1
        self.start()

    def logMe(self, txt):
        # print("LOG ME", txt)
        self.log.info('user: '+ txt)

    def logBot(self, mode, txt):
        # print("LOG BOT", txt)
        self.log.info('bot'+str(mode)+': '+txt)

    def start(self):
        # print("BOT LOG START")
        start = datetime.datetime.now().strftime("%d%m%Y_%H%M%S_")
        self.filename = '../logs/'+start+str(self.count)+'.log'
        self.count = self.count + 1
        # print("NEW LOG", self.filename)

        if(self.init):
            self.log.info('Conversation end')
            filehandler = logging.FileHandler(self.filename, 'w')
            formatter = logging.Formatter('%(asctime)s _ %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
            filehandler.setFormatter(formatter)
            self.log = logging.getLogger("conversation")
            self.log.propagate = False
            for hdlr in self.log.handlers[:]:
                if isinstance(hdlr,logging.FileHandler):
                    self.log.removeHandler(hdlr)
            self.log.addHandler(filehandler)
            self.log.setLevel(logging.INFO)
        else:
            filehandler = logging.FileHandler(self.filename, 'w')
            formatter = logging.Formatter('%(asctime)s _ %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
            filehandler.setFormatter(formatter)
            self.log = logging.getLogger("conversation")
            self.log.propagate = False
            self.log.addHandler(filehandler)
            self.log.setLevel(logging.INFO)
            self.init = True

        self.log.info('Conversation start')

    def stop(self):
        self.log.info('Conversation end')


if __name__ == '__main__':
    b = BotLog();
    b.logMe("ok")
    b.logBot("sdgsdgg")
    b.start()
    b.logMe("tetsetet")
    b.logBot("sdoif oisdjfodifjsdo ij")
