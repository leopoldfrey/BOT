#!/bin/sh

cd $(dirname $0)

echo "Installing python 3.9"
brew install python@3.9

echo "Installing virtualenv"
pip install virtualenv

echo "Creating bot virtual environnement"
virtualenv --python=/opt/homebrew/bin/python3.9 botenv

echo "Entering virtual env"
source ./botenv/bin/activate

echo "Installing dependencies"
pip install -r ./requirements.txt

echo "Done"
