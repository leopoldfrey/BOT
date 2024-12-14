#!/usr/bin/env pwsh
Set-Location $PSScriptRoot

Write-Output "Starting Editor"
Set-Location ./Editor
python ./Editor.py
