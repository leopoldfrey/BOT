#!/bin/sh

cd $(dirname $0)

echo "Installing virtualenv"
pip install virtualenv

echo "Creating bot virtual environnement"
virtualenv botenv

echo "Entering virtual env"
source ./botenv/bin/activate

echo "Installing dependencies"
pip install -r ./requirements.txt

echo "Done"
