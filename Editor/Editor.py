#!/usr/bin/env python3
import os, json, webbrowser, html, sys, glob
from bottle import post, static_file, template, Bottle, request
from sys import platform as _platform
from subprocess import Popen
import requests

sys.path.insert(0, '../Server')

import threading

#data_path = "../data/"
                         
import functools
print = functools.partial(print, flush=True)

class BotEditor():
    def __init__(self, data="../data/default.json"):

        #print("[Editor] Loading data...")

        self.filename = data
        self.load()

        #print("Loading data done.")

        print("[Editor] ___STARTING GOOGLE CHROME___")
        url = 'http://localhost:17995/'
        # MacOS
        if _platform == "darwin":
            chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
            webbrowser.get(chrome_path).open(url)
        elif _platform == "win32" or _platform == "win64":
            Popen(['C:\Program Files\Google\Chrome\Application\chrome.exe','http://localhost:17995'])
        # Linux
        # chrome_path = '/usr/bin/google-chrome %s'

        print("[Editor] Bot Editor starting...")
        self.host = '127.0.0.1'
        self.port = int(os.environ.get("PORT", 17995))
        self.server = Bottle()
        self.route()
        self.start()

    def changeFile(self, f):
        self.filename = f
        self.load()

    def load(self):
        print("[Editor] Loading data "+self.filename)
        with open(self.filename) as f:
            self.data = json.load(f)

        #print(self.data)

    def start(self):
        # démarrage du serveur
        self.server.run(host=self.host, port=self.port)

    def route(self):
        self.server.route('/', method="GET", callback=self.index)
        self.server.route('/index', method="GET", callback=self.index)
        self.server.route('/index.html', method="GET", callback=self.index)
        self.server.route('/<dir>/<filename>', method="GET", callback=self.serveDir)
        self.server.route('/<filename>', method="GET", callback=self.serve)

        self.server.route('/getSentences', method="GET", callback=self.getSentences)
        self.server.route('/getSequence', method="GET", callback=self.getSequence)
        self.server.route('/getSettings', method="GET", callback=self.getSettings)

        self.server.route('/modSentence', method="POST", callback=self.modSentence)
        self.server.route('/modSequence', method="POST", callback=self.modSequence)
        self.server.route('/save', method="POST", callback=self.save)
        self.server.route('/clear', method="POST", callback=self.clear)
        self.server.route('/delSequence', method="POST", callback=self.deleteSequence)
        self.server.route('/delSentence', method="POST", callback=self.deleteSentence)

        self.server.route('/openFile', method="POST", callback=self.openFile)
        self.server.route('/saveFile', method="POST", callback=self.saveFile)

    def index(self):
        return static_file('index.html', root='./')

    def serveDir(self, dir, filename):
        return static_file(filename, root='./'+dir)

    def serve(self, filename):
        return static_file(filename, root='./')
    
    def openFile(self):
        #print("OPEN FILE")
        for k in request.forms:
            self.data = json.loads(k)
        self.save()
        return { "msg": "Fichier ouvert"}

    def saveFile(self):
        for k in request.forms:
            fn = k
        #print("SAVING FILE TO:", "../data/"+fn+".json")
        with open("../data/"+fn+".json", "w") as f:
            f.truncate(0)
            f.seek(0)
            json.dump(self.data, f, indent=4)
        return { "msg": "Sauvegarde effectuée"}

    def getSentences(self):
        return self.data['sentences']

    def getSequence(self):
        return self.data['sequence']

    def getSettings(self):
        return self.data['settings']

    def save(self):
        with open(self.filename, "w") as f:
            f.truncate(0)
            f.seek(0)
            json.dump(self.data, f, indent=4)
        return { "msg": "Sauvegarde effectuée"}

    def clear(self):
        self.data = {}
        return { "msg": "Clear done"}

    def modSentence(self):
        for k in request.forms:
            j = json.loads(k)
            idx = html.unescape(j['idx'])
            #print("modSentence",idx)
            self.data['sentences'][idx] = j['sentence'].split(";")
            
            self.save()

        return { "msg": "Modification effecuée"}

    def modSequence(self):
        for k in request.forms:
            j = json.loads(k)
            idx = html.unescape(j['idx'])
            #print("modSequence",idx)

            if idx not in self.data:
                self.data['sequence'][idx] = {'prompt':'', 'first': '', 'nb_inter' : '', 'dur_max': '', 'option': ''}
                
            self.data['sequence'][idx]['prompt'] = j['prompt']
            self.data['sequence'][idx]['first'] = j['first']
            self.data['sequence'][idx]['nb_inter'] = j['nb_inter']
            #self.data['sequence'][idx]['dur_max'] = j['dur_max']
            self.data['sequence'][idx]['option'] = j['option']
            
            self.save()

        return { "msg": "Modification effecuée"}

    def deleteSentence(self):
        for k in request.forms:
            idx = html.unescape(json.loads(k)['idx'])
            del self.data['sentences'][idx]
            self.save()
        return { "msg": "Suppression effectuée"}

    def deleteSequence(self):
        for k in request.forms:
            idx = html.unescape(json.loads(k)['idx'])
            del self.data['sequence'][idx]
            self.save()
        return { "msg": "Suppression effectuée"}

if __name__ == "__main__":
    try:
        if len(sys.argv) == 2:
            server = BotEditor(data=sys.argv[1])
        else:
            server = BotEditor()
    
    except KeyboardInterrupt:
        pass
    finally:
        os._exit(0)
