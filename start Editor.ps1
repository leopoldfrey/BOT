#!/usr/bin/env pwsh
cd $PSScriptRoot

echo "Entering Virtual Env"
./botenv/bin/Activate.ps1
echo "Starting Editor"
cd ./Editor
python3 ./Editor.py