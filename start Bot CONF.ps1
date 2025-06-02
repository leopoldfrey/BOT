#!/usr/bin/env pwsh
[Console]::TreatControlCAsInput = $True

$host.UI.RawUI.ForegroundColor = "cyan"
Write-Output "Starting Server"
Start-Job -Name Server  -WorkingDirectory $PSScriptRoot/Server -ScriptBlock {
  python ./BotServer2.py
}

$host.UI.RawUI.ForegroundColor = "Yellow"
Write-Output "Starting Brain"
Start-Job -Name Brain -WorkingDirectory $PSScriptRoot/Server -ScriptBlock {
  Start-Sleep -Seconds 1;
  python ./BotBrain.py ../data/default_conf.json
}

While (Get-Job -State "Running")
{
  $host.UI.RawUI.ForegroundColor = "Yellow"
  Receive-Job -Name Brain
  $host.UI.RawUI.ForegroundColor = "cyan"
  Receive-Job -Name Server
  Start-Sleep -Seconds 0.01
  If ($Host.UI.RawUI.KeyAvailable -and ($Key = $Host.UI.RawUI.ReadKey("AllowCtrlC,NoEcho,IncludeKeyUp"))) {
    If ([Int]$Key.Character -eq 3) {
      $host.UI.RawUI.ForegroundColor = "White"
      Write-Output "Shutting down"
      Stop-Job -Name Server
      Stop-Job -Name Brain
      Remove-Job -Name Server
      Remove-Job -Name Brain
    }
  }
}

$host.UI.RawUI.ForegroundColor = "White"
[Console]::TreatControlCAsInput = $False
Write-Output "End"