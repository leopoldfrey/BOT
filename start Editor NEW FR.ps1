#!/usr/bin/env pwsh
Set-Location $PSScriptRoot

Write-Output "Entering Virtual Env"
./botenv/bin/Activate.ps1

Write-Output "Starting Editor"
Set-Location ./Editor
python3 ./Editor.py ../data/default_FR.json
