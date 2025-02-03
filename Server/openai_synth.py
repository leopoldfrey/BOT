#!/usr/bin/env python3
import os, sys, time, json
from openai import OpenAI
from sys import platform as _platform
from threading import Thread
import subprocess
from pathlib import Path

import re
# if _platform == "darwin":
#     from playsound import playsound
import functools
print = functools.partial(print, end='\n',flush=True)

VOICE = []

API_KEY_PATH = "../secret/openai_api_key.json"

with open(API_KEY_PATH) as json_data:
    data = json.load(json_data)
os.environ['OPENAI_API_KEY'] = data['key']

client = OpenAI()

def get_voices():
    return VOICE

def get_voices(lang):
    return VOICE

class TextToSpeech(Thread):
    def __init__(self, text, silent=False):
        Thread.__init__(self)
        print("[Server] [TextToSpeech]",len(text), text)
        if(len(text) > 200):
            self.textA = re.split("[.!?;:]", text)
        else:
            self.textA = []
            self.textA.append(text)
        print("SPLIT", self.textA)
        self._running = True
        self.silent = silent
        self.pid = 0

    def stop(self):
        # print("TODO STOP VOICE", self.pid)
        self.textA = []
        if(self.pid != 0):
            if _platform == "darwin":
                subprocess.Popen(["kill", str(self.pid)])
            else:
                subprocess.Popen(["taskkill", "/PID", str(self.pid)])
        # pass

    def run(self):
        t = self.textA.pop(0)
        while t != "":
        # for t in self.textA :
            if t != "" and t != " ":
                print(">> speak", t)
                speech_file_path = Path(__file__).parent / "openai_speech.mp3"
                with client.audio.speech.with_streaming_response.create(
                    model="tts-1",
                    voice="onyx",
                    input=t,
                ) as response:
                    response.stream_to_file(speech_file_path)

                if self.silent:
                    return

                if _platform == "darwin":
                    self.proc = subprocess.Popen(["./ffplay","-nodisp","-autoexit","-loglevel","quiet","openai_speech.mp3"])
                    self.pid = self.proc.pid
                    # print("process pid", self.pid)
                    self.proc.wait()
                    # while (self.proc.poll() is None):
                    #     print("wait")
                    #     time.sleep(1)
                    #playsound('processed-output.wav')
                elif _platform == "win32" or _platform == "win64":
                    self.proc = subprocess.Popen(["ffplay.exe","-nodisp","-autoexit","-loglevel","quiet","openai_speech.mp3"])
                    self.pid = self.proc.pid
                    # print("process pid", self.pid)
                    self.proc.wait()
                    #os.system("ffplay.exe -nodisp -autoexit -loglevel quiet .\processed-output.wav")
            if len(self.textA) > 0:
                t = self.textA.pop(0)
            else:
                return

from time import sleep

if __name__ == '__main__':
    if len(sys.argv) == 2:
        thd = TextToSpeech(sys.argv[1])
        thd.start()
    else:
        text = "cuelgue por favor"
        thd = TextToSpeech(text = text)
        thd.start()
        sleep(5)
        #print('usage: %s <text-to-synthesize>')

