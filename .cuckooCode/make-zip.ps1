Add-Type -AssemblyName System.IO.Compression.FileSystem
$ErrorActionPreference = 'Stop'
$base = Get-Location
$src = Join-Path $base 'products\arabic-ai-prompts-300'
$dst = Join-Path $base 'products\arabic-ai-prompts-300.zip'
if (Test-Path $dst) { Remove-Item $dst -Force }
[System.IO.Compression.ZipFile]::CreateFromDirectory($src, $dst, [System.IO.Compression.CompressionLevel]::Optimal, $false)
Write-Host "DONE: $dst"
Get-Item $dst | Select-Object Name, Length, LastWriteTime | Format-List