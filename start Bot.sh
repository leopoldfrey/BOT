#!/bin/sh

cd $(dirname $0)

source ./botenv/bin/activate
  
cd ./Server
echo "Starting Sound"
python ./BotSound.py &

echo "Starting Server"
python ./BotServer.py &

sleep 2

echo "Starting Brain"
python ./BotBrain.py &