#!/usr/bin/env python3

from pyosc import Client, Server
from botLog import BotLog
import os, signal, functools, socket, json, sys, random
from unidecode import unidecode
from difflib import SequenceMatcher
from openai import OpenAI

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def asint(s):
    try: return int(s), ''
    except ValueError: return sys.maxint, s

print = functools.partial(print, end='\n',flush=True)

serverIP = "127.0.0.1"

API_KEY_PATH = "../secret/openai_api_key.json"
api_key = ""

SIMILAR = 0.85

with open(API_KEY_PATH) as json_file:
    json_data = json.load(json_file)
    api_key = json_data['key']

def contains(str, substr):
    if substr:
        substr_len = len(substr)
        for i in range(len(str)):
            if str[i:i+substr_len] == substr:
                return True
    return False

class BotBrain:
    # initialisation de la classe
    def __init__(self, data="../data/default.json"):
        # récupération de l'IP de la machine
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.ip = s.getsockname()[0]
        self.model = "ft:gpt-4o-mini-2024-07-18:personal:quijote-10interactions:AwdjqR1Y:ckpt-step-1408"
        s.close()

        self.osc_server = Server(self.ip, 14001, self.oscIn)
        self.osc_client = Client(serverIP, 14000) #"127.0.0.1"
        self.osc_client.send("/ip", self.ip)

        self.log = BotLog()
        self.curStep = 0
        self.curPart = 0

        self.ai_prefix = "Don Quijote:"
        self.human_prefix = "Sancho:"

        self.def_prompt = "Tu eres Don Quijote de la Mancha de Cervantes, acabas de despertar en 2024, con resaca de mal humor y enfadado e intentas actualizarte haciendo preguntas sobre el mundo actual.  Intentas saber donde se encuentran las grandes aventuras de caballeros hoy, y buscas un nuevo escudero para acompanarte en tus futuras aventuras. Hablas con frases cortas, directas, con humor y a la primera persona. Haces preguntas a tu interlocutor para saber si podria ser un buen escudero para acompnarte en las proximas hazanas."

        self.adios = ["adios", "adíos", "hasta luego", "nos vemos pronto", "hasta pronto", "hasta mañana", "hasta la vista", "ciao", "voy a colgar", "cuelgo" ]
        self.llm = OpenAI(api_key=api_key)

        self.filename = data
        self.loadData()

        print("[BotBrain] Ready",self.ip)

    def resetMemory(self):
        print("RESET MEMORY")
        self.memory = []

    def setPrompt(self, prompt):
        self.conversation_prompt = prompt
        #print("SET NEW PROMPT", self.conversation_prompt)

        if not self.memory:
            self.memory.append({"role": "system", "content": prompt})
        else:
            if self.memory[0]['role'] == 'system':
                self.memory[0]['content'] = prompt
            else:
                self.memory.insert(0, {"role": "system", "content": prompt})
        print(self.memory)

    def addPrompt(self, prompt):
        self.setPrompt(self.def_prompt+" "+prompt)
        print(self.def_prompt)
        print(prompt)

    def loadData(self):
        print("[BotBrain] Loading data")
        self.sequence = []
        self.relaunch = []
        self.goodbyes = []
        with open(self.filename) as f:
            data = json.load(f)
            seq = data["sequence"]
            self.sequence = [seq[k] for k in sorted(seq, key=asint)]
            self.relaunch = data['sentences']["relaunch"]
            self.goodbyes = data['sentences']["goodbyes"]
            self.human_prefix = data['settings']['username']
            self.ai_prefix = data['settings']['botname']
            self.model = data['settings']['model']

        #print("\tSequence:", type(self.sequence), self.sequence)
        #print("\t0:", self.sequence[0])
        self.def_prompt = self.sequence[0]['prompt']
        self.resetMemory()
        self.setPrompt(self.def_prompt)

    # initalisation de conversation déclenchée par le controleur principal (quand on décroche le téléphone)
    def newConversation(self):
        self.curStep = 0
        self.curPart = 1
        print("CURRENT PART", self.curPart, self.sequence[self.curPart])
        print("\t------> video", self.sequence[self.curPart]['video'])
        self.osc_client.send('/video',int(self.sequence[self.curPart]['video']))
        self.resetMemory()
        self.addPrompt(self.sequence[self.curPart]['prompt'])
        self.log.start()

    # première phrase du bot, c'est lui qui lance la conversation
    def speakStart(self):
        self.lastresponse = self.sequence[self.curPart]['first']
        if(self.lastresponse == ""):
            self.getResponse("")
        else:
            self.log.logBot(self.curPart, self.lastresponse)
            self.osc_client.send('/lastresponse',self.lastresponse)

    def preProcess(self, phrase):
        if phrase.startswith(" "):
            phrase = phrase[1:]
        return unidecode(phrase.lower())

    def checkAdios(self, phrase):
        found = False
        for i in range(len(self.adios)):
            if phrase.rfind(self.adios[i]) != -1:
                found = True

        if found:
            print("ADIOS!")
            return True
        else:
            return False

    # c'est ici qu'il faut insérer le BOT, string "phrase" en entrée
    def getResponse(self, phrase):
        phrase = self.preProcess(phrase)

        if self.checkAdios(phrase):
            self.endConversation(phrase)
            return None

        print("[BotBrain] user:",phrase)

        self.log.logMe(phrase)

        self.curStep += 1
        print(">>", self.curStep, "/", self.sequence[self.curPart]['nb_inter'])
        if self.curStep > int(self.sequence[self.curPart]["nb_inter"]) and int(self.sequence[self.curPart]["nb_inter"] != -1):
            self.curPart += 1
            self.curStep = 0
            try:
                print("CURRENT PART", self.curPart, self.sequence[self.curPart])
                print("\t------> interaction", self.sequence[self.curPart]['nb_inter'])
                #print("\t------> duration", self.sequence[self.curPart]['dur_max'])
                print("\t------> video", self.sequence[self.curPart]['video'])
                self.osc_client.send('/video',int(self.sequence[self.curPart]['video']))
                print("\t------> prompt", self.sequence[self.curPart]['prompt'])
                if(self.sequence[self.curPart]['prompt']):
                    self.addPrompt(self.sequence[self.curPart]['prompt'])
                else:
                    print("ERROR ! NO PROMPT !")
                if(self.sequence[self.curPart]["first"]):
                    self.lastresponse = self.sequence[self.curPart]['first']
                    self.log.logBot(self.curPart, self.lastresponse)
                    self.osc_client.send('/lastresponse',self.lastresponse)
                else:
                    print("NO FIRST, GENERATING...")
            except IndexError:
                print("ERROR, NO MORE PARTS")
                self.endConversation(phrase)
                #self.lastresponse = 'adelante Sancho, hablamos luego!'
                #self.log.logBot(self.curPart, self.lastresponse)
                #self.osc_client.send('/end',self.lastresponse)
                return None

        prev = self.lastresponse

        self.memory.append({"role": "user", "content": phrase})
        print(self.memory)
        completion = self.llm.chat.completions.create(
                model=self.model,
                messages=self.memory,
                temperature = 1,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
        self.lastresponse = completion.choices[0].message.content
        self.memory.append({"role": "assistant", "content": self.lastresponse})
        self.log.logBot(self.curPart, self.lastresponse)
        self.osc_client.send('/lastresponse', self.lastresponse)


    def postProcess(self, str):
        return (str.split("Sancho :")[0]).split("Sancho:")[0]


    # fin de conversation déclenchée par le controleur principal (temps max ou nombre d'interactions max)
    def endConversation(self, phrase):
        self.lastresponse = random.choice(self.goodbyes)
        self.log.logBot(self.curPart, self.lastresponse)
        self.osc_client.send('/end',self.lastresponse)

    # phrase(s) de relance quand silence trop long
    def relance(self):
        self.lastresponse = random.choice(self.relaunch)
        self.log.logBot(self.curPart, self.lastresponse)
        self.osc_client.send('/lastresponse', self.lastresponse)

    # phrase(s) que dit le bot quand il perd l'utilisateur
    def areYouThere(self):
        self.lastresponse = random.choice(self.relaunch)
        self.log.logBot(self.curPart, self.lastresponse)
        self.osc_client.send('/lastresponse', self.lastresponse)

# NE PAS MODIFIER SOUS CETTE LIGNE
# NE PAS MODIFIER SOUS CETTE LIGNE
# NE PAS MODIFIER SOUS CETTE LIGNE

    #messages reçus par le contrôleur principal
    def oscIn(self, address, *args):
        #print("OSC IN ", address, args[0])
        if(address == '/getresponse'):
            self.getResponse(args[0])
        elif(address == '/newConversation'):
            self.newConversation()
        elif(address == '/relance'):
            self.relance()
        elif(address == '/start'):
            self.speakStart()
        elif(address == '/end'):
            self.endConversation(args[0])
        elif(address == '/areYouThere'):
            self.areYouThere()
        elif(address == '/reload'):
            self.loadData()
        elif(address == '/model'):
            self.model = args[0]
            print("NEW MODEL", self.model)
            self.resetMemory()
            self.setPrompt(self.conversation_prompt)
        elif(address == '/botname'):
            self.ai_prefix = args[0]
        elif(address == '/username'):
            self.human_prefix = args[0]
        elif(address == '/end_prompt'):
            self.endPrompt = args[0]
        else:
            pass
            '''print("[BotBrain] OSC IN : "+str(address))
            for x in range(0,len(args)):
                print("     " + str(args[x]))'''

    # terminaison
    def kill(self):
        self.osc_server.stop()
        os._exit(0)

# gestion de terminaison de processus par signal
def handler(signum, frame):
    bot.kill()

signal.signal(signal.SIGINT, handler)

# MAIN
if __name__ == "__main__":
    if len(sys.argv) == 2:
        bot = BotBrain(data=sys.argv[1])
    else:
        bot = BotBrain()
