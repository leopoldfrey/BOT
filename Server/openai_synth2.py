#!/usr/bin/env python3
import os, sys, time, json
from openai import OpenAI
from sys import platform as _platform
from threading import Thread
import subprocess
import pyaudio 
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
    def __init__(self, text, stream, silent=False):
        Thread.__init__(self)
        print("[Server] [TextToSpeech]",len(text), text)
        #if(len(text) > 200):
        #    self.textA = re.split("[.!?;:]", text)
        #else:
        self.textA = []
        self.textA.append(text)
        #print("SPLIT", self.textA)
        self._running = True
        self.silent = silent
        self.pid = 0
        self.player_stream = stream

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
                #start_time = time.time() 
                player_stream = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=24_000, output=True) 
                with client.audio.speech.with_streaming_response.create( 
                    model="tts-1", 
                    voice="onyx", 
                    response_format="pcm",  # similar to WAV, but without a header chunk at the start.
                    input=t, 
                ) as response: 
                    #print(f"Time to first byte: {int((time.time() - start_time) * 1000)}ms") 
                    for chunk in response.iter_bytes(chunk_size=1024): 
                        if chunk:
                            self.player_stream.write(chunk)
                    #print(f"Done in {int((time.time() - start_time) * 1000)}ms.") 
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

