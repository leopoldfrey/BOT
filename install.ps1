#!/usr/bin/env pwsh

[Console]::TreatControlCAsInput = $True
# [System.Environment]::OSVersion.Platform

cd $PSScriptRoot

echo "Installing virtualenv"

pip install virtualenv

echo "Creating bot virtual environnement"

virtualenv botenv

echo "Entering virtual env"

./botenv/bin/Activate.ps1

echo "Installing dependencies"

pip install -r ./requirements.txt

echo "Done"
