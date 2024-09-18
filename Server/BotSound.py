#!/usr/bin/env python3
import pygame, time, random, os, json, sys
from pyosc import Server
import functools
print = functools.partial(print, end='\n',flush=True)

#sound_path = "../sounds/"
#configFilename = "soundconfig.json"

CHANNEL_AMBIANT_A = 0
CHANNEL_AMBIANT_B = 1
CHANNEL_BOTTINK = 2
CHANNEL_PHONE = 3

class BotSound():
    def __init__(self, data="../data/default.json"):
        self.botthinkCopy = None
        self.channel = CHANNEL_AMBIANT_B
        self.config = {}
        with open(data, 'r') as f:
            data = json.load(f)
            self.config = data["sound"]
        print("[Sound] Configuration :", self.config)
        self.sound_path = self.config['path']
        print("SOUND PATH", self.sound_path)
        pygame.mixer.init()
        self.loadSounds()
        self.osc_server = Server('127.0.0.1', 14004, self.oscIn)

    def loadSounds(self):
        print("[Sound] Load Sounds")
        self.phoneRing = pygame.mixer.Sound(self.sound_path + "phoneRing.wav")
        self.phoneRing.set_volume(self.config['ring'])
        self.phoneHang = pygame.mixer.Sound(self.sound_path + "phoneHang.wav")
        self.phoneHang.set_volume(self.config['hang'])
        self.section1 = pygame.mixer.Sound(self.sound_path + "1.intro.wav")
        self.section1.set_volume(self.config['ambiant'])
        self.section2 = pygame.mixer.Sound(self.sound_path + "2.seduction.wav")
        self.section2.set_volume(self.config['ambiant'])
        self.section3 = pygame.mixer.Sound(self.sound_path + "3.intermede.wav")
        self.section3.set_volume(self.config['ambiant'])
        self.section4 = pygame.mixer.Sound(self.sound_path + "4.provocation.wav")
        self.section4.set_volume(self.config['ambiant'])
        self.section5 = pygame.mixer.Sound(self.sound_path + "5.fuite.wav")
        self.section5.set_volume(self.config['ambiant'])
        self.section6 = pygame.mixer.Sound(self.sound_path + "6.epilogue.wav")
        self.section6.set_volume(self.config['ambiant'])
        self.end =      pygame.mixer.Sound(self.sound_path + "7.final.wav")
        self.end.set_volume(self.config['final'])

        self.botthink = []
        for j in os.listdir(self.sound_path):
            if j.__contains__('bot'):
                s = pygame.mixer.Sound(self.sound_path + j)
                s.set_volume(self.config['botthink'])
                self.botthink.append(s)
        self.botthinkCopy = self.botthink.copy()

    def oscIn(self, address, *args):
        if(address == '/phase'):
            self.botThink(args[0])
        elif(address == '/section'):
            self.section(args[0])
        elif(address == '/stop'):
            self.stop(args[0])
        elif(address == '/phone'):
            self.phone(args[0])
        else:
            print("[Sound] OSC IN : "+str(address))
            for x in range(0,len(args)):
                print("[Sound]      " + str(args[x]))

    def phone(self, action):
        pygame.mixer.Channel(CHANNEL_PHONE).stop()
        if action == 'ring':
            pygame.mixer.Channel(CHANNEL_PHONE).play(self.phoneRing, loops=-1)
        elif action == 'hang':
            pygame.mixer.Channel(CHANNEL_PHONE).play(self.phoneHang, loops=-1)
        else:
            pass

    def section(self, section):
        print("[Sound] Play", section)
        if section == 1:
            print("[Sound] Play Intro")
            self.xfade(self.section1)
        elif section == 2:
            print("[Sound] Play Séduction")
            self.xfade(self.section2)
        elif section == 3:
            print("[Sound] Play Intermède")
            self.xfade(self.section3)
        elif section == 4:
            print("[Sound] Play Provocation")
            self.xfade(self.section4)
        elif section == 5:
            print("[Sound] Play Fuite")
            self.xfade(self.section5)
        elif section == 6:
            print("[Sound] Play Épilogue")
            self.xfade(self.section6)
        else:
            self.stop(0)

    def botThink(self, phase):
        if phase == 1 :
            # print("[Sound] Play botThink")
            pygame.mixer.Channel(CHANNEL_BOTTINK).stop()
            if(len(self.botthinkCopy) == 0):
                self.botthinkCopy = self.botthink.copy()
            idx = random.randrange(len(self.botthinkCopy))
            currentThink = self.botthinkCopy.pop(idx)
            pygame.mixer.Channel(CHANNEL_BOTTINK).play(currentThink)
        elif phase == 2 :
            pygame.mixer.Channel(CHANNEL_BOTTINK).fadeout(self.config['botthinkFadeOut'])
        else:
            pass

    def stop(self, end):
        if end == 0: #USER LEFT
            print("[Sound] Stop")
            if self.channel == CHANNEL_AMBIANT_A :
                pygame.mixer.Channel(CHANNEL_AMBIANT_A).fadeout(self.config['stopFadeOut'])
            else:
                pygame.mixer.Channel(CHANNEL_AMBIANT_B).fadeout(self.config['stopFadeOut'])
            time.sleep(self.config['stopFadeOut']/1000)
            pygame.mixer.Channel(CHANNEL_AMBIANT_A).stop()
            pygame.mixer.Channel(CHANNEL_AMBIANT_B).stop()
            pygame.mixer.Channel(CHANNEL_BOTTINK).stop()
            self.channel == CHANNEL_AMBIANT_B
            print("[Sound] Stopped")

        else: #END ANIMATION
            print("[Sound] Play End File")
            self.xfade(self.end, loop=0)

    def xfade(self, newsound, loop=-1):
        if self.channel == CHANNEL_AMBIANT_A :
            self.channel = CHANNEL_AMBIANT_B
            pygame.mixer.Channel(CHANNEL_AMBIANT_A).fadeout(self.config['fadeOutMs'])
            pygame.mixer.Channel(CHANNEL_AMBIANT_B).play(newsound, loops=loop, fade_ms=self.config['fadeInMs'])
        else:
            self.channel = CHANNEL_AMBIANT_A
            pygame.mixer.Channel(CHANNEL_AMBIANT_B).fadeout(self.config['fadeOutMs'])
            pygame.mixer.Channel(CHANNEL_AMBIANT_A).play(newsound, loops=loop, fade_ms=self.config['fadeInMs'])

if __name__ == '__main__':
    if len(sys.argv) == 2:
        BotSound(data=sys.argv[1])
    else:
        BotSound()
