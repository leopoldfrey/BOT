#!/usr/bin/env python3
import bottle, os, time, json, webbrowser, sys
from subprocess import Popen
from sys import platform as _platform
from bottle import static_file
from gtts_synth import TextToSpeech
from threading import Thread
from websocket_server import WebsocketServer
from pyosc import Client, Server
from deepl_trans import translateFR, translateES, translate

import functools
print = functools.partial(print, flush=True)

DEBUG = True

import google.cloud.texttospeech as tts

MAXRING = 30
LANGUAGE = "es-ES"
DEF_VOICE = "es-ES-Neural2-F"

class ThreadGroup(Thread):
    def __init__(self, parent):
        Thread.__init__(self)
        self.thread_group = []
        self.parent = parent;

    def addThread(self, t):
        self.thread_group.append(t)

    def stop(self):
        for t in self.thread_group[:]:
            t.stop()

    def run(self):
        while True:
            for t in self.thread_group[:]:
                if not t.is_alive(): #isAlive
                    # self.parent.video_client.send("/botspeak", 0)
                    self.parent.video_client.send("/phase", 0)
                    self.parent.sound_client.send("/phase", 0)
                    self.parent.lastInteractionTime = time.time()
                    # print("END OF SYNTH THREAD")
                    self.thread_group.remove(t)
                    if(self.parent.on == False):
                        # print("OFF!!!")
                        pass
                    elif(self.parent.flagUserLost == True):
                        print("[Server] USER LOST")
                        self.flagWaitUser = False
                        self.parent.areYouThere()
                    elif(self.parent.flagWaitUser == True):
                        print("[Server] WAIT USER")
                        self.parent.silent = False
                        self.parent.wsServer.broadcast({'command':'silent','value':False})
                    elif(self.parent.flagWaitEnd == True):
                        print("[Server] WAIT END")
                        self.parent.silent = True
                        self.parent.wsServer.broadcast({'command':'silent','value':True})
                    else:
                        # print("REDONNE LA PAROLE !!!")
                        self.parent.silent = False
                        self.parent.wsServer.broadcast({'command':'silent','value':False})

class BotWebSocket(Thread):
    def __init__(self, parent):
        Thread.__init__(self)
        self.port=9001
        self.parent = parent
        self.server = WebsocketServer(port=self.port)
        self.server.set_fn_new_client(self.new_client)
        self.server.set_fn_client_left(self.client_left)
        self.server.set_fn_message_received(self.message_received)

    def broadcast(self, message):
        try:
            self.server.send_message_to_all(json.dumps(message))
        except BrokenPipeError:
            print("(BrokenPipeError)")

    # Called for every client connecting (after handshake)
    def new_client(self, client, server):
        # print("[ws] Client(%d) connected" % client['id'])
        self.broadcast({"command":"message","value":"Connection established"})
        self.broadcast({"command":"on","value":self.parent.on})
        self.broadcast({"command":"phone","value":self.parent.phone})
        self.broadcast({"command":"voices","value":self.parent.list_voices})
        self.broadcast({"command":"lang", "value":self.parent.lang})
        self.broadcast({
            'command':'params',
            'max_silence':self.parent.config["max_silence"],
            'max_relance_quit':self.parent.config["max_relance_quit"],
            'max_inter':self.parent.config["max_inter"],
            'max_inter_s':self.parent.config["max_inter_s"],
            'speed':self.parent.config["speed"],
            'pitch':self.parent.config["pitch"],
            'voice':self.parent.config['voice'],
            'lang':self.parent.config['lang'],
            'model':self.parent.config["model"],
            'botname':self.parent.config['botname'],
            'username':self.parent.config['username'],
            'end_prompt':self.parent.config['end_prompt']
        })

    # Called for every client disconnecting
    def client_left(self, client, server):
    	#print("[ws] Client(%d) disconnect
        # ed" % client['id'])
        pass

    # Called when a client sends a message
    def message_received(self, client, server, message):
        # if len(message) > 200:
        # 	message = message[:200]+'..'
        print("[Server] [ws] %s (%d)" % (message, client['id']))
        msg = json.loads(message)
        # print(msg["command"])
        if msg["command"] == "connect" :
            self.parent.wsServer.broadcast({'command':'silent','value':self.parent.silent})
        elif msg["command"] == "pause" :
            self.parent.pause()
        elif msg["command"] == "reset" :
            self.userDetected = False
            self.parent.reset()
        elif msg["command"] == "stop" :
            self.userDetected = False
            self.parent.reset()
        elif msg["command"] == "getConfig" :
            self.parent.getConfig()
        elif msg["command"] == "getVoices" :
            self.parent.getVoices()
        elif msg["command"] == "saveConfig" :
            self.parent.config["max_silence"] = int(msg["max_silence"])
            self.parent.config["max_relance_quit"] = int(msg["max_relance_quit"])
            self.parent.config["pitch"] = float(msg["pitch"])
            self.parent.config["speed"] = float(msg["speed"])
            self.parent.config["voice"] = msg["voice"]
            self.parent.config["lang"] = msg["lang"]
            self.parent.config["model"] = msg["model"]
            self.parent.config["botname"] = msg["botname"]
            self.parent.config["username"] = msg["username"]
            self.parent.config["end_prompt"] = msg["end_prompt"]
            self.parent.saveConfig()
        elif msg["command"] == "phone" :
            if(int(msg["phone"]) == 1):
                self.parent.phoneOn()
            else:
                self.parent.phoneOff()
        elif msg["command"] == "facedetect" :
            self.parent.facedetect(int(msg["facedetect"]))
        elif msg["command"] == "voice" :
            self.parent.voiceEnable(int(msg["voice"]))
        elif msg["command"] == "end" :
            self.parent.end()
        elif msg["command"] == "reload" :
            self.parent.tg.stop()
            self.userDetected = False
            self.parent.phone = False
            self.parent.end()
            self.parent.readConfig()
            self.parent.osc_client.send("/reload", 1)

    def run(self):
        self.server.run_forever()

    def stop(self):
        self.server.stop()

class BotServer:
    global is_restart_needed

    def __init__(self, http_server_port=8080, settings='../data/default.json'):
        #init
        self.http_server_port = http_server_port
        self.on = False
        self.phone = False
        self.silent = True
        self.username = ""
        self.startTime = time.time()
        self.lastInteractionTime = time.time()
        self.globalTime = 0
        self.currentTime = 0
        self.ringTime = 0
        self.interactions = 0
        self.is_restart_needed = True
        self.tmp_response = ""
        self.flagUserLost = False
        self.flagWaitUser = False
        self.flagWaitEnd = False
        self.waitHangPhone = False
        self.relanceCount = 0
        self.userDetected = False
        self.voice = DEF_VOICE
        self.voiceOn = False
        self.lang = LANGUAGE
        client = tts.TextToSpeechClient()
        voices = client.list_voices()
        self.list_voices = []
        for voice in voices.voices:
            if self.lang in voice.language_codes:
                self.list_voices.append(voice.name)
        #print("VOICES", self.list_voices)

        print("[Server] ___INIT TextToSpeech___")
        TextToSpeech("Botophone", silent=True).start()

        # print("[Server] ___INIT_RING___")
        # self.phoneCtrl = PhoneCtrl()

        #websocket
        print("[Server] ___STARTING WEBSOCKETSERVER___")
        self.wsServer = BotWebSocket(self)
        self.wsServer.start()

        #threadgroup (pour surveiller la fin de la synthèse vocale)
        print("[Server] ___INIT THREADGROUP___")
        self.tg = ThreadGroup(self)
        self.tg.start()

        print("[Server] ___STARTING OSC___")
        self.osc_server = Server('0.0.0.0', 14000, self.oscIn)
        self.osc_client = Client('127.0.0.1', 14001)
        self.video_server = Server('127.0.0.1', 14002, self.video_oscIn)
        self.video_client = Client('127.0.0.1', 14003)
        self.sound_client = Client('127.0.0.1', 14004)
        self.led_client = Client('127.0.0.1', 14005)

        #read from settings.json
        print("[Server] ___READING CONFIG___", settings)
        self.config = {
            "max_inter": 30,
            "max_inter_s": 300,
            "max_silence": 7,
            "max_relance_quit": 4,
            "pitch": 0.0,
            "speed": 1.00,
            "voice": "es-ES-Neural2-F",
            "lang": "es-ES",
            "model": "ft:mistral-small-latest:a8c72c9e:20240627:1267b6a8",
            "botname": "bot",
            "username": "user",
            "end_prompt": "\n\nResumen de conversación:\n{history}\nConversación actual:\n{chat_history_lines}\nSancho: {input}\nDon Quijote:"
        }
        self.settingsFile = settings #'settings.json'
        self.readConfig()

        print("[Server] ___INIT BOT___")
        self.osc_client.send('/newConversation',1)

        print("[Server] ___CONFIGURING SERVER___")
        self.http_server = bottle.Bottle()
        self.http_server.get('/', callback=self.index)
        self.http_server.get('/viewer', callback=self.viewer)
        self.http_server.get('/viewer.html', callback=self.viewer)
        self.http_server.get('/style.css', callback=self.css)
        self.http_server.post('/reco', callback=self.reco)
        self.http_server.get('/poll', callback=self.poll)
        # print()
        # print('*** Please open chrome at http://127.0.0.1:%d' % self.http_server_port)
        # print()

        # ouverture de google chrome
        print("")
        print("!!!")
        print("!!! SEE chrome://flags/#unsafely-treat-insecure-origin-as-secure TO ENABLE MICROPHONE !!!")
        print("!!!")
        print("")
        print("[Server] ___STARTING GOOGLE CHROME___")
        url = 'http://localhost:8080/'
        # MacOS
        if _platform == "darwin":
            chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
            webbrowser.get(chrome_path).open(url)
        elif _platform == "win32" or _platform == "win64":
            Popen(['C:\Program Files\Google\Chrome\Application\chrome.exe','http://localhost:8080'])
        # Linux
        # chrome_path = '/usr/bin/google-chrome %s'

        #démarrage du serveur
        print("[Server] ___STARTING SERVER___")
        self.http_server.run(host='0.0.0.0', port=self.http_server_port, quiet=True)

    def video_oscIn(self, address, *args):
        # print("[Server] VIDEO OSC IN ", address, args[0])
        # print("VIDEO OSC IN ", address, args[0])
        if(address == '/facedetect'):
            self.facedetect(int(args[0]))
        elif(address == '/end'):
            if int(args[0]) == 1 : #fin vidéo finale
                self.end()

    def oscIn(self, address, *args):
        #print("[Server] OSC IN ", address, args[0])
        if(address == '/lastresponse'):
            self.receiveResponse(args[0])
        elif(address == '/end'):
            self.receiveResponse(args[0])
            self.endDialog()
        elif(address == '/video'):
            self.video_client.send("/section", args[0])
            self.sound_client.send("/section", args[0])
        elif(address == '/ip'):
            print("[Server] Brain IP :",str(args[0]))
            self.osc_client  = Client(args[0], 14001)
            self.osc_client.send("/ip", "Ip received")
        elif(address == '/phone'):
            if(args[0] == 1):
                self.phoneOn()
            else:
                self.phoneOff()
        else:
            print("[Server] OSC IN :",str(address))
            for x in range(0,len(args)):
                print("     ",str(args[x]))

    def end(self):
        self.flagWaitEnd = False
        print("[Server] END > RESTART")
        # self.led_client.send("/on", 0)
        self.sound_client.send("/stop", 0)
        self.userDetected = False
        self.reset()
        time.sleep(1)
        if self.phone :
            self.phoneHang()

    def endDialog(self):
        print("[Server] WAIT FOR END")
        self.flagWaitEnd = True
        self.silent = True
        self.wsServer.broadcast({'command':'silent','value':self.silent})
        self.video_client.send("/stop", 1) # déclenchement vidéo finale
        self.sound_client.send("/stop", 1)

    def facedetect(self, v):
        if self.on :
            if self.flagWaitEnd :
                return
            elif v == 1 :
                print("[Server] FACEDETECT User found")
                self.userDetected = True
                self.wsServer.broadcast({"command":"facedetect","value":self.userDetected})
                self.flagUserLost = False
                self.flagWaitUser = False
            else:
                self.userDetected = False
                self.wsServer.broadcast({"command":"facedetect","value":self.userDetected})
                if self.flagWaitUser :
                    return
                else:
                    print("[Server] FACEDETECT User lost")
                    self.flagUserLost = True
                    self.flagWaitUser = False
            return
        else:
            if v == 1 :
                self.userDetected = True
                self.wsServer.broadcast({"command":"facedetect","value":self.userDetected})
                print("[Server] FACEDETECT User detected")
                if self.phone :
                    self.waitHangPhone = True
                    self.phoneHang()
                else:
                    self.ringTime = time.time()
                    self.sound_client.send("/phone", "ring")
            else:
                self.userDetected = False
                self.wsServer.broadcast({"command":"facedetect","value":self.userDetected})
                if self.phone :
                    self.phoneHang()
                else:
                    # self.phoneCtrl.stop()
                    self.sound_client.send("/phone", "stop")

    def phoneOn(self):
        print("[Server] PHONE ON")
        if self.on or self.phone :
            return
        if self.userDetected == False:
            print("[Server] NO USER > RACCROCHEZ")
            self.phone = True
            self.phoneHang()
        else:
            self.reset()
            # self.phoneCtrl.stop()
            self.sound_client.send("/phone", "stop")
            self.on = True
            self.phone = True
            self.video_client.send("/phone", 1)
            self.wsServer.broadcast({"command":"phone","value":self.phone})
            self.wsServer.broadcast({"command":"on","value":self.on})
            self.wsServer.broadcast({'command':'silent','value':self.silent})
            self.wsServer.broadcast({"command":"facedetect","value":self.userDetected})

            time.sleep(1)
            self.start()

    def phoneOff(self):
        if self.phone == False:
            return
        print("[Server] PHONE OFF")
        if self.flagWaitEnd :
            self.phone = False
            self.video_client.send("/phone", 0)
        elif self.waitHangPhone :
            self.phone = False
            self.waitHangPhone = False
            # self.video_client.send("/phone", 0)
            # self.phoneCtrl.ring()
            # TODO COUNT PHONE RING
            self.ringTime = time.time()
            self.sound_client.send("/phone", "ring")
        elif self.on :
            # self.phoneCtrl.stop()
            self.sound_client.send("/phone", "stop")
            self.sound_client.send("/stop", 0)
            self.tg.stop()
            self.phone = False
            self.video_client.send("/phone", 0)
            self.silent = True
            self.userDetected = False
            self.reset()
        else:
            self.sound_client.send("/phone", "stop")
            self.sound_client.send("/stop", 0)
            self.tg.stop()
            self.phone = False
            self.video_client.send("/phone", 0)
            self.silent = True
        self.wsServer.broadcast({'command':'silent','value':self.silent})
        self.wsServer.broadcast({"command":"phone","value":self.phone})
        self.wsServer.broadcast({"command":"on","value":self.on})
        self.wsServer.broadcast({"command":"facedetect","value":self.userDetected})

    def phoneHang(self):
        print("[Server] RACCROCHEZ")
        # self.phoneCtrl.hang()
        self.sound_client.send("/phone", "hang")

    def reco(self):
        self.flagUserLost = False
        self.flagWaitUser = False
        result = {'transcript': str(bottle.request.forms.getunicode('transcript')),
                'confidence': float(bottle.request.forms.get('confidence', 0)),
                'sentence': int(bottle.request.forms.sentence)}
        mess = result['transcript']
        self.lastInteractionTime = time.time()
        if result['sentence'] == 1:
            # print("user:", mess)
            # self.lastInteractionTime = time.time()
            self.wsServer.broadcast({'command':'_user','value':mess})
            self.video_client.send("/user", mess)
            self.video_client.send("/phase", 1)
            self.sound_client.send("/phase", 1)
            self.silent = True
            self.relanceCount = 0
            self.wsServer.broadcast({'command':'silent','value':self.silent})
            # print("INTER", self.interactions)
            if(DEBUG):
                mess = translateES(mess)
            
            if self.interactions >= self.maxinter :
                self.osc_client.send("/end", mess)
            else :
                self.osc_client.send('/getresponse', mess)

        return ''

    def speak(self, txt):
        if self.voiceOn:
            # print("SPEAK", txt, "pitch", self.pitch, "speed", self.speed)
            tts = TextToSpeech(txt, pitch=self.pitch, speed=self.speed, voice=self.voice, lang=self.lang)
            tts.start()
            self.tg.addThread(tts)
        else:
            self.video_client.send("/phase", 0)
            self.sound_client.send("/phase", 0)
            self.lastInteractionTime = time.time()
            if(self.on == False):
                pass
            elif(self.flagUserLost == True):
                print("[Server] USER LOST")
                self.flagWaitUser = False
                self.areYouThere()
            elif(self.flagWaitUser == True):
                print("[Server] WAIT USER")
                self.silent = False
                self.wsServer.broadcast({'command':'silent','value':False})
            elif(self.flagWaitEnd == True):
                print("[Server] WAIT END")
                self.silent = True
                self.wsServer.broadcast({'command':'silent','value':True})
            else:
                # print("REDONNE LA PAROLE !!!")
                self.silent = False
                self.wsServer.broadcast({'command':'silent','value':False})

    def voiceEnable(self, v):
        self.voiceOn = v
        if self.voiceOn == False :
            self.tg.stop()

    def receiveResponse(self, r):
        if self.on and not self.flagWaitEnd:
            self.tmp_response = r
            if(self.flagUserLost):
                self.flagUserLost = False
                self.flagWaitUser = True
            # print("SERVER receiveResponse", self.tmp_response)
            self.video_client.send("/phase", 2)
            self.sound_client.send("/phase", 2)
            self.video_client.send("/bot", self.tmp_response)
            self.interactions += 1
            self.video_client.send("/interactions", self.interactions)
            self.lastInteractionTime = time.time()
            self.wsServer.broadcast({'command':'_bot','value':self.tmp_response})
            # print("INTERACTIONS", self.interactions % self.config["max_interactions"])
            if(DEBUG):
                print(">>", translateFR(self.tmp_response))
            self.speak(self.tmp_response)
        else:
            print("SERVER receiveResponse OFF", r)
            
    def areYouThere(self):
        self.osc_client.send("/areYouThere", 1)

    def relance(self):
        if(self.flagWaitUser):
            print("[Server] USER REALLY LOST > RESET")
            self.video_client.send("/stop", 0)
            self.sound_client.send("/stop", 0)
            self.userDetected = False
            self.phoneHang()
            self.reset()
        elif(self.flagUserLost):
            print("[Server] USER LOST")
            self.flagWaitUser = False
            self.areYouThere()
        else:
            print("[Server] Relance", self.relanceCount)
            if(self.relanceCount > self.config["max_relance_quit"]):
                print("[Server] Relance >",self.config["max_relance_quit"],">> RESET")
                self.video_client.send("/stop", 0)
                self.sound_client.send("/stop", 0)
                self.userDetected = False
                self.phoneHang()
                self.reset()
            else:
                self.silent = True
                self.wsServer.broadcast({'command':'silent','value':self.silent})
                self.lastInteractionTime = time.time()
                self.osc_client.send("/relance", 1)
                self.relanceCount += 1

    def start(self):
        print("[Server] start")
        self.silent = True
        self.wsServer.broadcast({'command':'silent','value':self.silent})
        self.lastInteractionTime = time.time()
        self.osc_client.send("/start", 1)

    def reset(self):
        print("[Server] RESET")
        self.on = False
        self.startTime = time.time()
        self.lastInteractionTime = time.time()
        self.interactions = 0
        self.flagUserLost = False
        self.flagWaitUser = False
        self.flagWaitEnd = False
        self.relanceCount = 0
        self.video_client.send("/interactions", self.interactions)
        self.wsServer.broadcast({'command':'clear'})
        self.wsServer.broadcast({'command':'silent','value':self.silent})
        self.wsServer.broadcast({"command":"phone","value":self.phone})
        self.wsServer.broadcast({"command":"on","value":self.on})
        self.wsServer.broadcast({"command":"facedetect","value":self.userDetected})
        self.silent = True
        self.osc_client.send("/newConversation", 1)
        #self.sound_client.send("/section", random.randrange(1,6))

    def name(self, name):
        self.username = name
        self.wsServer.broadcast({'command':'username','value':self.username})

    def updateTimers(self):
        if(self.phone == False and self.waitHangPhone == False and self.on == False and self.userDetected == True):
            #print("RING TIME",time.time() - self.ringTime)
            if(time.time() - self.ringTime > MAXRING and time.time() - self.ringTime < 6 * MAXRING):
                print("[Server] USER REALLY LOST > RESET")
                self.video_client.send("/stop", 0)
                self.sound_client.send("/stop", 0)
                self.userDetected = False
                self.phoneHang()
                self.reset()

        self.globalTime = time.time() - self.startTime
        self.currentTime = time.time() - self.lastInteractionTime
        if self.currentTime > self.config["max_silence"]:
            if(not self.silent):
                self.relance()
        if(self.globalTime > self.maxtime and not self.flagWaitEnd):
            self.osc_client.send("/end", "")
        #else:
        #    self.globalTime = 0
        #    self.currentTime = 0

        self.wsServer.broadcast({"command":"timers","global":self.globalTime, "current":self.currentTime, 'interactions':self.interactions, 'maxinter':self.maxinter})

    def poll(self):
        self.updateTimers()
        if self.is_restart_needed:
            self.is_restart_needed = False
            return {'restart':True};
        return {'restart':False};

    def index(self):
        return open("public/index.html", "rt").read()

    def viewer(self):
        return open("public/viewer.html", "rt").read()

    def css(self):
        return static_file("public/style.css", root="")

    def getConfig(self):
        self.wsServer.broadcast({
            'command':'params',
            'max_silence':self.config["max_silence"],
            'max_relance_quit':self.config["max_relance_quit"],
            'max_inter':self.config["max_inter"],
            'max_inter_s':self.config["max_inter_s"],
            'speed':self.config["speed"],
            'pitch':self.config["pitch"],
            'voice':self.config['voice'],
            'lang':self.config['lang'],
            'model':self.config["model"],
            'botname':self.config['botname'],
            'username':self.config['username'],
            'end_prompt':self.config['end_prompt']
        })

    def saveConfig(self):
        # print("CONFIG", self.config)
        with open(self.settingsFile, 'r') as f:
            jsonContent = json.load(f)
        with open(self.settingsFile, 'w') as f:
            jsonContent['settings'] = self.config
            json.dump(jsonContent, f, indent=4)
        self.updateParams()

    def readConfig(self):
        with open(self.settingsFile, 'r') as f:
            jsonContent = json.load(f)
            self.config = jsonContent['settings']

        print("Configuration:",self.config)
        self.updateParams()

    def getVoices(self):
        client = tts.TextToSpeechClient()
        voices = client.list_voices()
        self.list_voices = []
        for voice in voices.voices:
            if self.lang in voice.language_codes:
                self.list_voices.append(voice.name)
        #print("VOICES", self.list_voices)
        self.wsServer.broadcast({"command":"voices","value":self.list_voices})

    def updateParams(self):
        self.maxtime = self.config["max_inter_s"]
        self.maxinter = self.config["max_inter"]
        self.pitch = self.config["pitch"]
        self.speed = self.config["speed"]
        self.lang = self.config['lang']
        self.voice = self.config['voice']
        client = tts.TextToSpeechClient()
        voices = client.list_voices()
        self.list_voices = []
        for voice in voices.voices:
            if self.lang in voice.language_codes:
                self.list_voices.append(voice.name)
        #print("VOICES", self.list_voices)
        self.wsServer.broadcast({"command":"voices","value":self.list_voices})
        self.wsServer.broadcast({"command":"voice","value":self.voice})
        self.wsServer.broadcast({"command":"lang", "value":self.lang})
        self.osc_client.send("/model", self.config['model'])
        self.osc_client.send("/botname", self.config['botname'])
        self.wsServer.broadcast({"command":"botname", "value":self.config['botname']})
        self.osc_client.send("/username", self.config['username'])
        self.wsServer.broadcast({"command":"username", "value":self.config['username']})
        self.osc_client.send("/end_prompt", self.config['end_prompt'])

    def resume(self):
        self.silent = False
        self.wsServer.broadcast({'command':'silent','value':self.silent})

    def pause(self):
        self.silent = not self.silent
        self.wsServer.broadcast({'command':'silent','value':self.silent})

    def kill(self):
        print("[Server] Stop Video Osc Server")
        self.video_server.stop()
        print("[Server] Stop Brain Osc Server")
        self.osc_server.stop()
        os._exit(0)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        BotServer(settings=sys.argv[1])
    else:
        BotServer()
