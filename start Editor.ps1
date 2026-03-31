#!/usr/bin/env pwsh
Set-Location $PSScriptRoot

$PythonCmd = if ($IsWindows) { Join-Path $PSScriptRoot "botenv/Scripts/python.exe" } else { Join-Path $PSScriptRoot "botenv/bin/python" }
if (-not (Test-Path $PythonCmd)) {
  throw "Python virtual environment not found: $PythonCmd"
}
Write-Output "Using Python: $PythonCmd"

Write-Output "Starting Editor"
Set-Location ./Editor
& $PythonCmd ./Editor.py