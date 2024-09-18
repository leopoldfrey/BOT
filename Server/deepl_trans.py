#!/usr/bin/env python3
import sys
from deep_translator import GoogleTranslator

import functools
print = functools.partial(print, end='\n',flush=True)

def translateES(txt):
    return GoogleTranslator(source='fr', target='es').translate(text=txt)

def translateFR(txt):
    return GoogleTranslator(source='es', target='fr').translate(text=txt)

def translate(txt, src, dst):
    return GoogleTranslator(source=src, target=dst).translate(text=txt)

if __name__ == '__main__':
    print(translateES(sys.argv[1]))