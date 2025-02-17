#!/usr/bin/env python3

from pyosc import Client, Server
from botLog import BotLog
import os, signal, functools, socket, json, sys, random
from unidecode import unidecode
from difflib import SequenceMatcher

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

from langchain.chains import ConversationChain
from langchain.memory import (
    CombinedMemory,
    ConversationBufferMemory,
    ConversationBufferWindowMemory,

)
from langchain_core.prompts import PromptTemplate
from langchain_openai.chat_models import ChatOpenAI

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
        self.model = "ft:mistral-small-latest:a8c72c9e:20240627:1267b6a8"
        s.close()

        self.osc_server = Server(self.ip, 14001, self.oscIn)
        self.osc_client = Client(serverIP, 14000) #"127.0.0.1"
        self.osc_client.send("/ip", self.ip)

        self.log = BotLog()
        self.curStep = 0
        self.curPart = 0

        self.ai_prefix = "Don Quijote:"
        self.human_prefix = "Sancho:"
        self.endPrompt = """
        Conversación actual:
        {chat_history_lines}
        Sancho: {input}
        Don Quijote:"""

        self.def_prompt = "Tu eres Don Quijote de la Mancha de Cervantes, acabas de despertar en 2024, con resaca de mal humor y enfadado e intentas actualizarte haciendo preguntas sobre el mundo actual.  Intentas saber donde se encuentran las grandes aventuras de caballeros hoy, y buscas un nuevo escudero para acompanarte en tus futuras aventuras. Hablas con frases cortas, directas, con humor y a la primera persona. Haces preguntas a tu interlocutor para saber si podria ser un buen escudero para acompnarte en las proximas hazanas."

        self.adios = ["adios", "adíos", "hasta luego", "nos vemos pronto", "hasta pronto", "hasta mañana", "hasta la vista", "ciao", "chao", "voy a colgar", "cuelgo" ]

        self.filename = data
        self.loadData()

        print("[BotBrain] Ready",self.ip)

    def resetMemory(self):
        print("RESET MEMORY")
        self.conv_memory = ConversationBufferWindowMemory(k=50,
            memory_key="chat_history_lines", input_key="input",  ai_prefix=self.ai_prefix, human_prefix=self.human_prefix
        )
        self.memory = self.conv_memory

    def setPrompt(self, prompt):
        self.conversation_prompt = prompt
        print("SET NEW PROMPT", self.conversation_prompt)
        self.PROMPT = PromptTemplate(
            input_variables=["input", "chat_history_lines"],
            template=self.conversation_prompt,
        )
        print("WITH MODEL:", self.model)
        self.llm = ChatOpenAI(api_key=api_key, model=self.model, temperature=0.8, top_p=1, frequency_penalty=0, presence_penalty=0)
        self.conversation = ConversationChain(llm=self.llm, verbose=False, memory=self.memory, prompt=self.PROMPT)

    def addPrompt(self, prompt):
        self.conversation_prompt = self.def_prompt+" "+prompt+" "+self.endPrompt
        print("ADD NEW PROMPT", self.conversation_prompt)
        self.PROMPT = PromptTemplate(
            input_variables=["input", "chat_history_lines"],
            template=self.conversation_prompt,
        )
        self.conversation = ConversationChain(llm=self.llm, verbose=False, memory=self.memory, prompt=self.PROMPT)

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
            self.endPrompt = data['settings']['end_prompt']
            self.model = data['settings']['model']

        #print("\tSequence:", type(self.sequence), self.sequence)
        #print("\t0:", self.sequence[0])
        self.def_prompt = self.sequence[0]['prompt']
        self.resetMemory()
        self.setPrompt(self.def_prompt+self.endPrompt)

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
                    return None
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
        try:
            self.lastresponse = self.postProcess(self.conversation.invoke({"input": phrase})['response'])
            #CHECK REPETITION
            sim = similar(self.lastresponse, prev)
            while sim > SIMILAR:
                print("_____ SIMILARITY :",sim)
                self.lastresponse = self.postProcess(self.conversation.invoke({"input": phrase})['response'])
                sim = similar(self.lastresponse, prev)
        except:
            print("¡¡¡Error!!!")
            self.lastresponse = self.postProcess(self.conversation.invoke({"input": phrase})['response'])
        finally:
            print("[BotBrain]",self.curPart,self.lastresponse)
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
