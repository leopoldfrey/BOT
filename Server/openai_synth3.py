#!/usr/bin/env python3
import queue, json, os, sys
import threading
from threading import Thread
from functools import reduce
from typing import Callable, Generator

import openai
import pyaudio

#dummy
VOICE = []
def get_voices():
    return VOICE
def get_voices(lang):
    return VOICE

# Constants
DELIMITERS = [f"{d} " for d in (".", "?", "!")]  # Determine where one phrase ends
MINIMUM_PHRASE_LENGTH = 200  # Minimum length of phrases to minimize audio choppiness
TTS_CHUNK_SIZE = 2048

# Default values
DEFAULT_TTS_MODEL = "tts-1"
DEFAULT_VOICE = "onyx"

# Initialize OpenAI client.
API_KEY_PATH = "../secret/openai_api_key.json"
with open(API_KEY_PATH) as json_data:
    data = json.load(json_data)
os.environ['OPENAI_API_KEY'] = data['key']

OPENAI_CLIENT = openai.OpenAI()

p = pyaudio.PyAudio()
player_stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)


# Global stop event

class TextToSpeech(Thread):
    def __init__(self, text, silent=False):
        Thread.__init__(self)
        print("[Server] [TextToSpeech]",len(text), text)
        self.text = text
        self._running = True
        self.silent = silent
        self.pid = 0
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()

    def run(self):
        phrase_queue = queue.Queue()
        audio_queue = queue.Queue()

        phrase_generation_thread = threading.Thread(
            target=self.phrase_generator, args=(phrase_queue,self.text)
        )
        tts_thread = threading.Thread(
            target=self.text_to_speech_processor, args=(phrase_queue, audio_queue)
        )
        audio_player_thread = threading.Thread(target=self.audio_player, args=(audio_queue,))

        phrase_generation_thread.start()
        tts_thread.start()
        audio_player_thread.start()

        # Create and start the "enter to stop" thread. Daemon means it will not block
        # exiting the script when all the other (non doemon) threads have completed.
        #threading.Thread(target=self.wait_for_enter, daemon=True).start()

        phrase_generation_thread.join()
        #print("## all phrases enqueued. phrase generation thread terminated.")
        tts_thread.join()
        #print("## all tts complete and enqueued. tts thread terminated.")
        audio_player_thread.join()
        #print("## audio output complete. audio player thread terminated.")

    def stream_delimited_completion(
        self,
        working_string = "",
        content_transformers: list[Callable[[str], str]] = [],
        phrase_transformers: list[Callable[[str], str]] = [],
        delimiters: list[str] = DELIMITERS,
    ) -> Generator[str, None, None]:
        """Generates delimited phrases from OpenAI's chat completions."""

        def apply_transformers(s: str, transformers: list[Callable[[str], str]]) -> str:
            return reduce(lambda c, transformer: transformer(c), transformers, s)

        if self.stop_event.is_set():
            yield None
            return

        # Apply all transformers to the content before adding it to the working_string
        #working_string += apply_transformers(content, content_transformers)
        while len(working_string) >= MINIMUM_PHRASE_LENGTH:
            delimiter_index = -1
            for delimiter in delimiters:
                index = working_string.find(delimiter, MINIMUM_PHRASE_LENGTH)
                if index != -1 and (
                    delimiter_index == -1 or index < delimiter_index
                ):
                    delimiter_index = index

            if delimiter_index == -1:
                break

            phrase, working_string = (
                working_string[: delimiter_index + len(delimiter)],
                working_string[delimiter_index + len(delimiter) :],
            )
            yield apply_transformers(phrase, phrase_transformers)

        # Yield any remaining content that didn't end with the delimiter
        if working_string.strip():
            yield working_string.strip()

        yield None  # Sentinel value to signal "no more coming"


    def phrase_generator(self, phrase_queue: queue.Queue, text):
        """Generates phrases and puts them in the phrase queue."""
        
        for phrase in self.stream_delimited_completion(
            working_string=text,
            content_transformers=[
                lambda c: c.replace("\n", " ")
            ],  # If a line ends with a period, this helps it be recognized as a phrase.
            phrase_transformers=[
                lambda p: p.strip()
            ],  # Since each phrase is being used for audio, we don't need white-space
        ):
            # Sentinel (nothing more coming) signal received, so pass it downstream and exit
            if phrase is None:
                phrase_queue.put(None)
                return

            print(f"> {phrase}")
            phrase_queue.put(phrase)


    def text_to_speech_processor(
        self,
        phrase_queue: queue.Queue,
        audio_queue: queue.Queue,
        client: openai.OpenAI = OPENAI_CLIENT,
        model: str = DEFAULT_TTS_MODEL,
        voice: str = DEFAULT_VOICE,
    ):
        """Processes phrases into speech and puts the audio in the audio queue."""
        while not self.stop_event.is_set():
            phrase = phrase_queue.get()
            # Got the signal that nothing more is coming, so pass that down and exit
            if phrase is None:
                audio_queue.put(None)
                return

            try:
                with client.audio.speech.with_streaming_response.create(
                    model=model, voice=voice, response_format="pcm", input=phrase
                ) as response:
                    for chunk in response.iter_bytes(chunk_size=TTS_CHUNK_SIZE):
                        audio_queue.put(chunk)
                        if self.stop_event.is_set():
                            return
            except Exception as e:
                print(f"Error in text_to_speech_processor: {e}")
                audio_queue.put(None)
                return


    def audio_player(self, audio_queue: queue.Queue):
        """Plays audio from the audio queue."""

        #try:
        while not self.stop_event.is_set():
            audio_data = audio_queue.get()
            # got the sentinel value that there's nothing more coming, so exit
            if audio_data is None:
                break
            player_stream.write(audio_data)
        #except Exception as e:
        #    print(f"Error in audio_player: {e}")
        #finally:
        #    player_stream.stop_stream()
        #    player_stream.close()
        #    p.terminate()

if __name__ == "__main__":
    if len(sys.argv) == 2:
        thd = TextToSpeech(sys.argv[1])
        thd.start()
    else:
        text = "Pretende que estas enfadado y de mal humor. Pretende que estas harto de que la ficcion no se tome enserio. Pretende que vas a declarar el mundo ficcional como sola realidad. Y a la ficcion realidad. Y a la imaginacion la unica forma noble de pensamiento."
        thd = TextToSpeech(text = text)
        thd.start()
