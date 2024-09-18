#!/usr/bin/env pwsh

[Console]::TreatControlCAsInput = $True
# [System.Environment]::OSVersion.Platform

$host.UI.RawUI.ForegroundColor = "Magenta"
echo "Starting Sound"
$job1 = Start-Job -Name Sound -WorkingDirectory $PSScriptRoot/Server -ScriptBlock {
  ../botenv/bin/Activate.ps1
  python ./BotSound.py
}

$host.UI.RawUI.ForegroundColor = "cyan"
echo "Starting Server"
$job3 = Start-Job -Name Server  -WorkingDirectory $PSScriptRoot/Server -ScriptBlock {
    ../botenv/bin/Activate.ps1
    python ./BotServer.py
}

$host.UI.RawUI.ForegroundColor = "Yellow"
echo "Starting Brain"
$job2 = Start-Job -Name Brain -WorkingDirectory $PSScriptRoot/Server -ScriptBlock {
    Start-Sleep -Seconds 2;
    ../botenv/bin/Activate.ps1
    python ./BotBrain.py
}

While (Get-Job -State "Running")
{
  $host.UI.RawUI.ForegroundColor = "Magenta"
  Receive-Job -Name Sound
  $host.UI.RawUI.ForegroundColor = "Yellow"
  Receive-Job -Name Brain
  $host.UI.RawUI.ForegroundColor = "cyan"
  Receive-Job -Name Server
  Start-Sleep -Seconds 0.01
  If ($Host.UI.RawUI.KeyAvailable -and ($Key = $Host.UI.RawUI.ReadKey("AllowCtrlC,NoEcho,IncludeKeyUp"))) {
    If ([Int]$Key.Character -eq 3) {
      $host.UI.RawUI.ForegroundColor = "White"
      echo "Shutting down"
      Stop-Job -Name Server
      Stop-Job -Name Brain
      Stop-Job -Name Sound
      Remove-Job -Name Server
      Remove-Job -Name Brain
      Remove-Job -Name Sound
    }
  }
}

$host.UI.RawUI.ForegroundColor = "White"
[Console]::TreatControlCAsInput = $False
echo "End"
