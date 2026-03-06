# Plan: LLM Streaming → Sentence-by-Sentence TTS

## Context

Currently `BotBrain._invoke()` waits for the full LLM response before returning. The full text is sent via OSC `/lastresponse` → `BotServer.speak()` → `TextToSpeech`. The user waits for the entire generation before hearing any speech.

Goal: stream the LLM response, detect sentence boundaries in real time, and start synthesizing + playing each sentence as soon as it's complete.

**Current flow:**
```
_invoke() → [wait full response] → postProcess() → OSC /lastresponse → speak(full_text)
```

**Target flow:**
```
_invoke_streaming() → sentence1 → OSC /sentence → TTS queue → play sentence1
                    → sentence2 → OSC /sentence → TTS queue → play sentence2 (after 1)
                    → OSC /lastresponse (full text, for history/UI display only)
```

---

## Files Modified

- `Server/BotBrain.py`
- `Server/BotServer.py`

---

## BotBrain.py Changes

### 1. Add `import re` at top

### 2. Add `_invoke_streaming(phrase)` generator after `_invoke()` (line 142)

```python
def _invoke_streaming(self, phrase):
    """Generator that yields translated sentences as the LLM streams tokens."""
    BOUNDARY = re.compile(r'(?<=[.!?])\s+(?=[A-ZÁÀÂÇÉÈÊËÎÏÔÙÛÜÑ¿¡])')
    messages = (
        [{"role": "system", "content": self.system_prompt}]
        + self.history
        + [{"role": "user", "content": phrase}]
    )
    provider = _detect_provider(self.model)
    params = {"model": self.model, "messages": messages,
              "temperature": 0.8, "max_tokens": 400, "stream": True}
    if provider != "claude":
        params.update({"top_p": 1, "frequency_penalty": 0.3, "presence_penalty": 0.6})

    buffer = ""
    for chunk in self.client.chat.completions.create(**params):
        delta = chunk.choices[0].delta.content
        if delta is None:
            continue
        buffer += delta
        # Early stop if model starts the next human turn
        for marker in ["Sancho :", "Sancho:"]:
            if marker in buffer:
                buffer = buffer[:buffer.index(marker)]
                if buffer.strip():
                    yield self.postProcess(buffer.strip())
                return
        # Yield complete sentences on boundary
        parts = BOUNDARY.split(buffer)
        for sentence in parts[:-1]:
            s = self.postProcess(sentence.strip())
            if s.strip():
                yield s
        buffer = parts[-1]
    # Flush remainder
    if buffer.strip():
        s = self.postProcess(buffer.strip())
        if s.strip():
            yield s
```

### 3. Replace `getResponse()` core block (lines 225–255)

Replace the block starting at `prev = self.lastresponse` through `self.osc_client.send('/lastresponse', ...)`:

```python
prev = self.lastresponse
sentences = []
try:
    _t0 = time.time()
    for sentence in self._invoke_streaming(phrase):
        sentences.append(sentence)
        self.osc_client.send('/sentence', sentence)
    self.lastresponse = " ".join(sentences)
    print(f"[BotBrain] model time (stream): {time.time()-_t0:.2f}s")

    # Repetition check on full accumulated response
    count = 0
    sim = similar(self.lastresponse, prev)
    while sim > SIMILAR:
        print("_____ SIMILARITY:", sim, "- retrying")
        self.osc_client.send('/cancel_speech', 1)
        sentences = []
        _t0 = time.time()
        for sentence in self._invoke_streaming(phrase):
            sentences.append(sentence)
            self.osc_client.send('/sentence', sentence)
        self.lastresponse = " ".join(sentences)
        print(f"[BotBrain] model time (retry): {time.time()-_t0:.2f}s")
        sim = similar(self.lastresponse, prev)
        count += 1
        if count > 5:
            break
except:
    print("¡¡¡Error!!!")
    self.osc_client.send('/cancel_speech', 1)
    _t0 = time.time()
    self.lastresponse = self.postProcess(self._invoke(phrase))
    print(f"[BotBrain] model time (fallback): {time.time()-_t0:.2f}s")
finally:
    self.history.append({"role": "user", "content": phrase})
    self.history.append({"role": "assistant", "content": self.lastresponse})
    if len(self.history) > 100:
        self.history = self.history[2:]
    print("[BotBrain]", self.curPart, self.lastresponse)
self.log.logBot(self.curPart, self.lastresponse)
self.osc_client.send('/lastresponse', self.lastresponse)
```

---

## BotServer.py Changes

### 1. Add `import queue` at top

### 2. Add to `__init__()` (after `self.tg = ...`)

```python
self._tts_queue = queue.Queue()
self._current_tts = None
self._sentence_streaming = False
self._tts_worker_thread = Thread(target=self._tts_worker_loop, daemon=True)
self._tts_worker_thread.start()
```

### 3. Add `_tts_worker_loop()` method

```python
def _tts_worker_loop(self):
    while True:
        item = self._tts_queue.get()
        if item is None:
            break
        txt, is_end_sentinel = item
        if not is_end_sentinel:
            tts = TextToSpeech(txt, lang=self.lang, voice=self.voice)
            self._current_tts = tts
            tts.start()
            tts.join()
            self._current_tts = None
        else:
            # All sentences played — fire "end of speech" callbacks
            self.sound_client.send("/phase", 0)
            self.lastInteractionTime = time.time()
            if not self.on:
                pass
            elif self.flagWaitEnd:
                self.silent = True
                self.end()
                self.wsServer.broadcast({'command': 'silent', 'value': True})
            elif self.flagUserLost:
                self.flagWaitUser = False
                self.areYouThere()
            elif self.flagWaitUser:
                self.silent = False
                self.wsServer.broadcast({'command': 'silent', 'value': False})
            else:
                self.silent = False
                self.wsServer.broadcast({'command': 'silent', 'value': False})
        self._tts_queue.task_done()
```

### 4. Add `receiveSentence(sentence)` method

```python
def receiveSentence(self, sentence):
    if self.on and not self.flagWaitEnd:
        self._sentence_streaming = True
        print("[Server] receiveSentence:", sentence[:60])
        self._tts_queue.put((sentence, False))
```

### 5. Add `cancelSpeech()` method

```python
def cancelSpeech(self):
    print("[Server] cancelSpeech: draining TTS queue")
    if self._current_tts is not None:
        self._current_tts.stop()
    while not self._tts_queue.empty():
        try:
            self._tts_queue.get_nowait()
            self._tts_queue.task_done()
        except queue.Empty:
            break
    self._sentence_streaming = False
```

### 6. Modify `oscIn()` — add two branches before the `else`

```python
elif address == '/sentence':
    self.receiveSentence(args[0])
elif address == '/cancel_speech':
    self.cancelSpeech()
```

### 7. Modify `receiveResponse()` — replace `self.speak(self.tmp_response)` (line 544)

```python
if self._sentence_streaming:
    self._tts_queue.put(("", True))  # end-of-stream sentinel triggers callbacks
    self._sentence_streaming = False
else:
    self.speak(self.tmp_response)
```

---

## Backward Compatibility

- `_invoke()` unchanged — fallback exception path still uses it
- `speak()` and `ThreadGroup` unchanged — used by relance, areYouThere, speakStart, endConversation (all send `/lastresponse` without `/sentence`, so `_sentence_streaming` is False)
- `/lastresponse` still sent at end for UI display and history

## Verification

1. Start BotServer + BotBrain
2. Trigger a user phrase
3. Logs should show sentences arriving and audio starting before full LLM response completes
4. Verify no audio overlap between sentences
5. Test interrupt (speak while bot is talking) → TTS queue drains cleanly
6. Test relance/areYouThere → still work via the non-streaming path
