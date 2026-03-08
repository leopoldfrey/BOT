#!/usr/bin/env python3
import sys
import base64, functools, subprocess, json, os, re, requests
from sys import platform as _platform
from threading import Thread

print = functools.partial(print, end='\n', flush=True)

INWORLD_ENDPOINT = "https://api.inworld.ai/tts/v1/voice"

def _load_key(path):
    with open(path) as f:
        return json.load(f)["key"]

_api_key = _load_key("../secret/inworld_api_key.json")

class TextToSpeech(Thread):
    def __init__(self, text, pitch=0.0, speed=1.0, voice="Olivia", silent=False, lang="fr-FR", on_chunk=None):
        Thread.__init__(self)
        text = text.replace('\u2019', "'").replace('\u2018', "'")
        chunks = re.split(r'(?<=[.!?])\s+(?=[A-ZÁÀÂÇÉÈÊËÎÏÔÙÛÜ])', text.strip())
        self.textA = [c for c in chunks if c.strip()]
        if not self.textA:
            self.textA = [text]
        print("[Inworld] chunks:", self.textA)
        self.voice = voice
        self.speed = max(0.5, min(1.5, speed))  # clamp to valid range
        self.silent = silent
        self.pid = 0
        self.on_chunk = on_chunk

    def stop(self):
        self.textA = []
        if self.pid != 0:
            if _platform == "darwin":
                subprocess.Popen(["kill", str(self.pid)])
            else:
                subprocess.Popen(["taskkill", "/PID", str(self.pid)])

    def run(self):
        if not self.textA or self.silent:
            return
        for i, chunk in enumerate(self.textA):
            if not self.textA:  # stop() was called
                break
            chunk = chunk.capitalize()
            print("[Inworld] synthesizing:", chunk[:60])
            response = requests.post(
                INWORLD_ENDPOINT,
                headers={
                    "Authorization": f"Basic {_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "text": chunk,
                    "voiceId": self.voice,
                    "modelId": "inworld-tts-1.5-max",
                    "talkingSpeed": self.speed,
                },
            )
            response.raise_for_status()
            audio_bytes = base64.b64decode(response.json()["audioContent"])
            filename = f"inworld-output-{i}.mp3"
            with open(filename, "wb") as f:
                f.write(audio_bytes)
            if _platform == "darwin":
                self.proc = subprocess.Popen(["./ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filename])
            else:
                self.proc = subprocess.Popen(["ffplay.exe", "-nodisp", "-autoexit", "-loglevel", "quiet", filename])
            self.pid = self.proc.pid
            self.proc.wait()
            if self.on_chunk:
                self.on_chunk(chunk)  # 👈 broadcast après synthèse
            try:
                os.remove(filename)
            except OSError:
                pass

if __name__ == '__main__':
    if len(sys.argv) == 3:
        thd = TextToSpeech(sys.argv[1], voice=sys.argv[2])
        thd.start()
    else:
        print("Usage: inworld_synth.py 'Text to speak' [VoiceName]")