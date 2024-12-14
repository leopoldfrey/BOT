#!/usr/bin/env pwsh
[Console]::TreatControlCAsInput = $True

$host.UI.RawUI.ForegroundColor = "Magenta"
Write-Output "Starting Sound"
Start-Job -Name Sound -WorkingDirectory $PSScriptRoot/Server -ScriptBlock {
  python ./BotSound.py
}

$host.UI.RawUI.ForegroundColor = "cyan"
Write-Output "Starting Server"
Start-Job -Name Server  -WorkingDirectory $PSScriptRoot/Server -ScriptBlock {
    python ./BotServer.py
}

$host.UI.RawUI.ForegroundColor = "Yellow"
Write-Output "Starting Brain"
Start-Job -Name Brain -WorkingDirectory $PSScriptRoot/Server -ScriptBlock {
  Start-Sleep -Seconds 3;
  python ./BotBrain.py
}

$host.UI.RawUI.ForegroundColor = "Green"
echo "Starting Unreal"
$job6 = Start-Job -Name LitteBotUnreal  -WorkingDirectory $PWD/LitteBotServer -ScriptBlock {
  Start-Sleep -Seconds 50;
   C:\PLASTIC\LITTLEBOT_EXPORT\WindowsNoEditor\FaceARSample.exe
}


While (Get-Job -State "Running")
{
  $host.UI.RawUI.ForegroundColor = "Magenta"
  Receive-Job -Name Sound
  $host.UI.RawUI.ForegroundColor = "Yellow"
  Receive-Job -Name Brain
  $host.UI.RawUI.ForegroundColor = "cyan"
  Receive-Job -Name Server
  $host.UI.RawUI.ForegroundColor = "Green"
  Receive-Job -Name LitteBotUnreal
  Start-Sleep -Seconds 0.01
  If ($Host.UI.RawUI.KeyAvailable -and ($Key = $Host.UI.RawUI.ReadKey("AllowCtrlC,NoEcho,IncludeKeyUp"))) {
    If ([Int]$Key.Character -eq 3) {
      $host.UI.RawUI.ForegroundColor = "White"
      Write-Output "Shutting down"
      Stop-Job -Name Server
      Stop-Job -Name Brain
      Stop-Job -Name Sound
      Stop-Job -Name LitteBotUnreal
      Remove-Job -Name Server
      Remove-Job -Name Brain
      Remove-Job -Name Sound
      Remove-Job -Name LitteBotUnreal
    }
  }
}

$host.UI.RawUI.ForegroundColor = "White"
[Console]::TreatControlCAsInput = $False
Write-Output "End"
