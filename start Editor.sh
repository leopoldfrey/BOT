#!/bin/sh
cd $(dirname $0)

echo "Entering Virtual Env"
source ./botenv/bin/activate

echo "Starting Editor"
cd ./Editor
python3 ./Editor.py