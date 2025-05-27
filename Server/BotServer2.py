#!/usr/bin/env python3
import bottle, os, time, json, webbrowser, sys
from subprocess import Popen
from sys import platform as _platform
from bottle import static_file
from gtts_synth import TextToSpeech
#from openai_synth3 import TextToSpeech
from threading import Thread
from websocket_server import WebsocketServer
from pyosc import Client, Server
#from deepl_trans import translateFR, translateES, translate
#import pyaudio

import functools
print = functools.partial(print, flush=True)

DEBUG = False
DEBUG2 = False

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
                    self.parent.lastInteractionTime = time.time()
                    print("END OF SYNTH THREAD")
                    self.thread_group.remove(t)
                    if(self.parent.on == False):
                        print("OFF!!!")
                        pass
                    else:
                        #self.parent.nextAnswer = False
                        time.sleep(2)
                        print("REDONNE LA PAROLE !!!")
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
        elif msg["command"] == "voice" :
            self.parent.voiceEnable(int(msg["voice"]))
        elif msg["command"] == "end" :
            self.parent.end()
        elif msg["command"] == "on" :
            if(msg["value"] == True):
                print("[Server] ON")
                self.parent.on = True
                self.parent.start()
            else:
                print("[Server] OFF")
                self.parent.on = False
                self.parent.reset()
        elif msg["command"] == "reload" :
            self.parent.reload()
        elif msg["command"] == "answer" :
            if self.parent.silent == False:
                print("[Server] ANSWER")
                self.parent.answer()

    def run(self):
        self.server.run_forever()

    def stop(self):
        self.server.stop()

class BotServer:
    global is_restart_needed

    def __init__(self, http_server_port=8080, settings='../data/default_conf.json'):
        #init
        self.http_server_port = http_server_port
        self.on = False
        self.silent = True
        self.username = ""
        self.startTime = time.time()
        self.lastInteractionTime = time.time()
        self.globalTime = 0
        self.currentTime = 0
        self.interactions = 0
        self.is_restart_needed = True
        self.tmp_response = ""
        self.voice = DEF_VOICE
        self.voiceOn = True
        self.lang = LANGUAGE
        self.lastMessage = ""
        #client = tts.TextToSpeechClient()
        #voices = client.list_voices()
        #self.list_voices = []
        #for voice in voices.voices:
        #    if "fr-FR" in voice.language_codes:
        #        self.list_voices.append(voice.name)
        #    if "es-ES" in voice.language_codes:
        #        self.list_voices.append(voice.name)
        #    if "en-GB" in voice.language_codes:
        #        self.list_voices.append(voice.name)
        #    if "en-US" in voice.language_codes:
        #       self.list_voices.append(voice.name)
            #if self.lang in voice.language_codes:
            #    self.list_voices.append(voice.name)
        #print("VOICES", self.list_voices)

        print("[Server] ___INIT TextToSpeech___")
        TextToSpeech("Hola", silent=True).start()
        
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
        self.http_server.get('/style2.css', callback=self.css2)
        self.http_server.get('/jquery-3.6.0.min.js', callback=self.js)
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
        url2 = 'http://localhost:8080/viewer.html'
        # MacOS
        if _platform == "darwin":
            #chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
            chrome_path = 'open -a /Applications/Google\ Chrome.app %s --args --kiosk --disable-infobars'
            webbrowser.get(chrome_path).open(url)
        elif _platform == "win32" or _platform == "win64":
            Popen(['C:\Program Files\Google\Chrome\Application\chrome.exe','--kiosk', '--disable-infobars', 'http://localhost:8080'])
        # Linux
        # chrome_path = '/usr/bin/google-chrome %s'


        #démarrage du serveur
        print("[Server] ___STARTING SERVER___")
        self.http_server.run(host='0.0.0.0', port=self.http_server_port, quiet=True)

    def oscIn(self, address, *args):
        #print("[Server] OSC IN ", address, args[0])
        if(address == '/lastresponse'):
            self.receiveResponse(args[0])
        elif(address == '/end'):
            self.receiveResponse(args[0])
            self.endDialog()
        elif(address == '/option'):
            pass
        elif(address == '/ip'):
            print("[Server] Brain IP :",str(args[0]))
            self.osc_client  = Client(args[0], 14001)
            self.osc_client.send("/ip", "Ip received")
        else:
            print("[Server] OSC IN :",str(address))
            for x in range(0,len(args)):
                print("     ",str(args[x]))

    def reload(self):
        self.tg.stop()
        self.end()
        self.readConfig()
        self.osc_client.send("/reload", 1)

    def end(self):
        print("[Server] END > RESTART")
        self.reset()

    def endDialog(self):
        print("[Server] WAIT FOR END")
        self.silent = True
        self.wsServer.broadcast({'command':'silent','value':self.silent})

    def reco(self):
        result = {'transcript': str(bottle.request.forms.getunicode('transcript')),
                'confidence': float(bottle.request.forms.get('confidence', 0)),
                'sentence': int(bottle.request.forms.sentence)}
        mess = result['transcript']
        self.lastInteractionTime = time.time()
        if result['sentence'] == 1:
            self.lastMessage = self.lastMessage + " " + mess
            # print("user:", mess)
            # self.lastInteractionTime = time.time()
            self.wsServer.broadcast({'command':'_user','value':self.lastMessage})
            # print("INTER", self.interactions)
            #if(DEBUG):
            #    mess = translateES(mess)
            # if self.nextAnswer:
            #     self.silent = True
            #     self.wsServer.broadcast({'command':'silent','value':self.silent})
            #     self.osc_client.send('/getresponse', self.lastMessage)
        return ''
    
    def answer(self):
        self.silent = True
        self.wsServer.broadcast({'command':'silent','value':self.silent})
        self.osc_client.send('/getresponse', self.lastMessage)
        self.lastMessage = ""

    def speak(self, txt):
        if self.voiceOn:
            tts = TextToSpeech(txt)
            tts.start()
            self.tg.addThread(tts)
        else:
            self.lastInteractionTime = time.time()
            if(self.on == False):
                pass
            else:
                # print("REDONNE LA PAROLE !!!")
                self.silent = False
                self.wsServer.broadcast({'command':'silent','value':False})

    def voiceEnable(self, v):
        self.voiceOn = v
        if self.voiceOn == False :
            self.tg.stop()

    def receiveResponse(self, r):
        if self.on:
            self.tmp_response = r
            # print("SERVER receiveResponse", self.tmp_response)
            self.interactions += 1
            self.lastInteractionTime = time.time()
            self.wsServer.broadcast({'command':'_bot','value':self.tmp_response})
            #if(DEBUG or DEBUG2):
            #    print(">>", translateFR(self.tmp_response))
            self.speak(self.tmp_response)
        else:
            print("SERVER receiveResponse OFF", r)

    def start(self):
        print("[Server] START")
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
        self.wsServer.broadcast({'command':'clear'})
        self.wsServer.broadcast({'command':'silent','value':self.silent})
        self.wsServer.broadcast({"command":"on","value":self.on})
        self.silent = True
        self.osc_client.send("/newConversation", 1)

    def name(self, name):
        self.username = name
        self.wsServer.broadcast({'command':'username','value':self.username})

    def updateTimers(self):
        self.globalTime = time.time() - self.startTime
        self.currentTime = time.time() - self.lastInteractionTime
        self.wsServer.broadcast({"command":"timers","global":self.globalTime, "current":self.currentTime, 'interactions':self.interactions, 'maxinter':self.maxinter})

    def poll(self):
        self.updateTimers()
        if self.is_restart_needed:
            self.is_restart_needed = False
            return {'restart':True};
        return {'restart':False};

    def index(self):
        return open("public/index2.html", "rt").read()

    def viewer(self):
        return open("public/viewer.html", "rt").read()

    def css(self):
        return static_file("public/style.css", root="")
    
    def css2(self):
        return static_file("public/style2.css", root="")

    def js(self):
        return static_file("public/jquery-3.6.0.min.js", root="")

    def getConfig(self):
        print(">> getConfig")
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
        print(">> saveConfig", self.config)
        with open(self.settingsFile, 'r') as f:
            jsonContent = json.load(f)
        with open(self.settingsFile, 'w') as f:
            jsonContent['settings'] = self.config
            json.dump(jsonContent, f, indent=4)
        #self.updateParams()
        self.reload()

    def readConfig(self):
        print(">> readConfig")
        with open(self.settingsFile, 'r') as f:
            jsonContent = json.load(f)
            self.config = jsonContent['settings']

        print("---- > Configuration:",self.config)
        self.updateParams()

    def getVoices(self):
        #client = tts.TextToSpeechClient()
        #voices = client.list_voices()
        self.list_voices = []
        #for voice in voices.voices:
        #    if "fr-FR" in voice.language_codes:
        #        self.list_voices.append(voice.name)
        #    if "es-ES" in voice.language_codes:
        #        self.list_voices.append(voice.name)
        #    if "en-GB" in voice.language_codes:
        #        self.list_voices.append(voice.name)
        #    if "en-US" in voice.language_codes:
        #        self.list_voices.append(voice.name)
            #if self.lang in voice.language_codes:
            #    self.list_voices.append(voice.name)
        #print("VOICES", self.list_voices)
        self.wsServer.broadcast({"command":"voices","value":self.list_voices})

    def updateParams(self):
        print(">> updateParams")
        self.maxtime = self.config["max_inter_s"]
        print("SET MAX TIME", self.maxtime)
        self.maxinter = self.config["max_inter"]
        print("SET MAX INTER", self.maxinter)
        self.pitch = self.config["pitch"]
        print("SET PITCH", self.pitch)
        self.speed = self.config["speed"]
        print("SET SPEED", self.speed)
        self.lang = self.config['lang']
        print("SET LANG", self.lang)
        self.voice = self.config['voice']
        print("SET VOICE", self.voice)

        #client = tts.TextToSpeechClient()
        #voices = client.list_voices()
        self.list_voices = []
        #for voice in voices.voices:
        #    if "fr-FR" in voice.language_codes:
        #        self.list_voices.append(voice.name)
        #    if "es-ES" in voice.language_codes:
        #        self.list_voices.append(voice.name)
        #    if "en-GB" in voice.language_codes:
        #        self.list_voices.append(voice.name)
        #    if "en-US" in voice.language_codes:
        #        self.list_voices.append(voice.name)
        #print("VOICES", self.list_voices)
        self.wsServer.broadcast({"command":"voices","value":self.list_voices})
        self.wsServer.broadcast({"command":"lang", "value":self.lang})
        self.wsServer.broadcast({"command":"voice","value":self.voice})
        self.osc_client.send("/model", self.config['model'])
        self.osc_client.send("/botname", self.config['botname'])
        print("SET BOTNAME", self.config['botname'])
        self.wsServer.broadcast({"command":"botname", "value":self.config['botname']})
        self.osc_client.send("/username", self.config['username'])
        print("SET USERNAME", self.config['username'])
        self.wsServer.broadcast({"command":"username", "value":self.config['username']})
        self.osc_client.send("/end_prompt", self.config['end_prompt'])

    def resume(self):
        self.silent = False
        self.wsServer.broadcast({'command':'silent','value':self.silent})

    def pause(self):
        self.silent = not self.silent
        self.wsServer.broadcast({'command':'silent','value':self.silent})

    def kill(self):
        print("[Server] Stop Brain Osc Server")
        self.osc_server.stop()
        os._exit(0)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        BotServer(settings=sys.argv[1])
    else:
        BotServer()
