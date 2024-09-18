#!/usr/bin/env pwsh

Set-Location $PSScriptRoot

Write-Output "Installing virtualenv"
pip install virtualenv

Write-Output "Creating bot virtual environnement"
virtualenv botenv

Write-Output "Entering virtual env"
./botenv/bin/Activate.ps1

Write-Output "Installing dependencies"
pip install -r ./requirements.txt

Write-Output "Done"
