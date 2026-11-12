$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root "agent\.venv\Scripts\pythonw.exe"
$Agent = Join-Path $Root "agent\main.py"
if (-not (Test-Path $Python)) { throw "Agent virtual environment not found. Run run_agent.bat once first." }
$Action = New-ScheduledTaskAction -Execute $Python -Argument ('"' + $Agent + '"') -WorkingDirectory (Join-Path $Root "agent")
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
Register-ScheduledTask -TaskName "Dragon S1 Agent" -Action $Action -Trigger $Trigger -Principal $Principal -Description "Visible Dragon S1 USB approval agent" -Force
Write-Host "Dragon S1 Agent scheduled task installed."
