#!/bin/sh

cd $(dirname $0)

source ./botenv/bin/activate
  
cd ./Server
echo "Starting Sound"
python ./BotSound.py ../data/default_FR.json &

echo "Starting Server"
python ./BotServer.py ../data/default_FR.json &

sleep 2

echo "Starting Brain"
python ./BotBrain.py ../data/default_FR.json &