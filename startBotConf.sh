#!/bin/sh

cd $(dirname $0)

source ./botenv/bin/activate
  
cd ./Server

echo "Starting Server"
python ./BotServer2.py &

sleep 1

echo "Starting Brain"
python ./BotBrain.py  .//data/default_conf.json &