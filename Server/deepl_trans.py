#!/usr/bin/env python3
import sys
from deep_translator import GoogleTranslator

import functools
print = functools.partial(print, end='\n',flush=True)

_translator_es = GoogleTranslator(source='fr', target='es')
_translator_fr = GoogleTranslator(source='es', target='fr')
_translator_fr2 = GoogleTranslator(target='fr')

def translateES(txt):
    return _translator_es.translate(text=txt)

def translateFR(txt):
    return _translator_fr.translate(text=txt)

def translateFR2(txt):
    return _translator_fr2.translate(text=txt)

def translate(txt, src, dst):
    return GoogleTranslator(source=src, target=dst).translate(text=txt)

if __name__ == '__main__':
    print(translateES(sys.argv[1]))