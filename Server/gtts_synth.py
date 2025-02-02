#!/usr/bin/env python3
import os, sys, time
import google.cloud.texttospeech as tts
from sys import platform as _platform
from threading import Thread
from pedalboard import *
from pedalboard.io import AudioFile
import subprocess
import re
# if _platform == "darwin":
#     from playsound import playsound
import functools
print = functools.partial(print, end='\n',flush=True)

VOICE = []

API_KEY_PATH = "../secret/gtts_api_key.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = API_KEY_PATH

# Make a Pedalboard object, containing multiple plugins:
board = Pedalboard([Gain(4),PitchShift(semitones=0)]) #Chorus(),Reverb(room_size=0.02,damping=0.1,wet_level=0.7,dry_level=1.,width=0.9,freeze_mode=0)

def get_voices():
    client = tts.TextToSpeechClient()
    voices = client.list_voices()

    for voice in voices.voices:
        if "fr-FR" in voice.language_codes:
            VOICE.append(voice.name)
        if "es-ES" in voice.language_codes:
            VOICE.append(voice.name)
        if "en-GB" in voice.language_codes:
            VOICE.append(voice.name)
        if "en-US" in voice.language_codes:
            VOICE.append(voice.name)
            #print(f"{voice.name}")
    
    print(VOICE)
    return VOICE

def get_voices(lang):
    client = tts.TextToSpeechClient()
    voices = client.list_voices()
    for voice in voices.voices:
        if lang in voice.language_codes:
            VOICE.append(voice.name)
    
    return VOICE

class TextToSpeech(Thread):
    def __init__(self, text, pitch=0.0, speed=1.08, voice="en-GB-Neural2-A", silent=False, lang="en-GB"):
        Thread.__init__(self)
        print("[Server] [TextToSpeech]", pitch, speed, voice)
        self.language_code = lang
        if(len(text) > 500):
            self.textA = re.split("[.!?;:]", text)
        else:
            self.textA = []
            self.textA.append(text)
        # print(len(self.textA), self.textA)
        self.voice = voice
        self.voice_params = tts.VoiceSelectionParams(
            language_code=self.language_code, name=self.voice
        )
        self.audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16, speaking_rate=speed, pitch=pitch)
        self.client = tts.TextToSpeechClient()
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
            self.text_input = tts.SynthesisInput(text=t)
            if t != "":
                # print("speak", t)
                response = self.client.synthesize_speech(
                    input=self.text_input, voice=self.voice_params, audio_config=self.audio_config
                )
                filename = "processed-output.wav"
                with open(filename, "wb") as out:
                    out.write(response.audio_content)

                # # Read in a whole audio file:
                # with AudioFile(filename, 'r') as f:
                #   audio = f.read(f.frames)
                #   samplerate = f.samplerate

                # # Run the audio through this pedalboard!
                # effected = board(audio, samplerate)

                # # Write the audio back as a wav file:
                # with AudioFile('processed-output.wav', 'w', samplerate, effected.shape[0]) as f:
                #   f.write(effected)

                if self.silent:
                    return

                if _platform == "darwin":
                    self.proc = subprocess.Popen(["./ffplay","-nodisp","-autoexit","-loglevel","quiet","processed-output.wav"])
                    self.pid = self.proc.pid
                    # print("process pid", self.pid)
                    self.proc.wait()
                    # while (self.proc.poll() is None):
                    #     print("wait")
                    #     time.sleep(1)
                    #playsound('processed-output.wav')
                elif _platform == "win32" or _platform == "win64":
                    self.proc = subprocess.Popen(["ffplay.exe","-nodisp","-autoexit","-loglevel","quiet","processed-output.wav"])
                    self.pid = self.proc.pid
                    # print("process pid", self.pid)
                    self.proc.wait()
                    #os.system("ffplay.exe -nodisp -autoexit -loglevel quiet .\processed-output.wav")
            if len(self.textA) > 0:
                t = self.textA.pop(0)
            else:
                return

class TextToSpeechNoThread():
    def __init__(self):
        #self.audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)
        self.client = tts.TextToSpeechClient()

    def synthesize(self, text, pitch=0.0, speed=1.08, voice="en-GB-Neural2-A", fname="output", play=True ,lang = "en-GB"):
        start = time.perf_counter()
        self.voice = voice
        self.language_code = lang
        self.voice_params = tts.VoiceSelectionParams(
            language_code=self.language_code, name=self.voice
        )
        self.audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16, speaking_rate=speed, pitch=pitch)
        self.text_input = tts.SynthesisInput(text=text)
        response = self.client.synthesize_speech(
            input=self.text_input, voice=self.voice_params, audio_config=self.audio_config
        )
        filename = "tmp.wav"
        with open(filename, "wb") as out:
            out.write(response.audio_content)

        # Read in a whole audio file:
        with AudioFile(filename, 'r') as f:
          audio = f.read(f.frames)
          samplerate = f.samplerate

        # Run the audio through this pedalboard!
        #effected = board(audio, samplerate)

        # Write the audio back as a wav file:
        proc_filename = fname+".wav"
        with AudioFile(proc_filename, 'w', samplerate, audio.shape[0]) as f:
          f.write(audio)

        end = time.perf_counter()
        print(f"Google Time to first chunk: {end-start}s", file=sys.stderr)

        if play:
            self.proc = subprocess.Popen(["ffplay","-nodisp","-autoexit","-loglevel","quiet",proc_filename])
            self.pid = self.proc.pid
            # print("process pid", self.pid)
            self.proc.wait()
            # os.system("ffplay.exe -nodisp -autoexit -loglevel quiet .\processed-output.wav")

from time import sleep

if __name__ == '__main__':
    if len(sys.argv) == 2:
        thd = TextToSpeech(sys.argv[1])
        thd.start()
    elif len(sys.argv) == 3:
        thd = TextToSpeech(sys.argv[1], voice=int(sys.argv[2]))
        thd.start()
    elif len(sys.argv) == 4:
        thd = TextToSpeech(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]))
        thd.start()
    elif len(sys.argv) == 5:
        thd = TextToSpeech(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]))
        thd.start()
        # print(thd.is_alive())
        # tts = TextToSpeechNoThread()
        # tts.synthesize(sys.argv[1])
    else:
        #v = get_voices("es-ES")
        v = ['es-ES-Neural2-B']
        text = "cuelgue por favor"
        sp = 1
        pi = 0
        for i in range(len(v)):
            #print(v[i])
            thd = TextToSpeech(text = text, pitch = pi, speed = sp, voice=v[i], lang='es-ES')
            thd.start()
            sleep(5)
        #print('usage: %s <text-to-synthesize>')

