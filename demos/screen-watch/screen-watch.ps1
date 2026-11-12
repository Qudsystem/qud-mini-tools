param(
  [int]$Fps = 15,
  [int]$Threshold = 40,
  [string]$OutFile = "events.jsonl",
  [int]$DurationSec = 30,
  [int]$DownScale = 4,
  [int]$MinChangedCells = 20
)

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms

$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$W = $screen.Width
$H = $screen.Height
$SW = [int]($W / $DownScale)
$SH = [int]($H / $DownScale)

if (-not [System.IO.Path]::IsPathRooted($OutFile)) {
  $OutFile = Join-Path (Get-Location) $OutFile
}

$startRec = [ordered]@{ meta='start'; ts=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds(); fps=$Fps; threshold=$Threshold; scale=$DownScale; screenW=$W; screenH=$H }
($startRec | ConvertTo-Json -Compress) | Out-File -FilePath $OutFile -Encoding UTF8

$interval = [int](1000 / $Fps)
$endTime = (Get-Date).AddSeconds($DurationSec)
$frame = 0
$prevBytes = $null
$prevStride = 0
$totalEvents = 0

$bmpFull = New-Object System.Drawing.Bitmap($W, $H)
$bmpSmall = New-Object System.Drawing.Bitmap($SW, $SH)
$gFull = [System.Drawing.Graphics]::FromImage($bmpFull)
$gSmall = [System.Drawing.Graphics]::FromImage($bmpSmall)

$rect = New-Object System.Drawing.Rectangle(0, 0, $SW, $SH)
$fmt = [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
$lockMode = [System.Drawing.Imaging.ImageLockMode]::ReadOnly

while ((Get-Date) -lt $endTime) {
  $gFull.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
  $gSmall.DrawImage($bmpFull, 0, 0, $SW, $SH)

  $data = $bmpSmall.LockBits($rect, $lockMode, $fmt)
  $stride = $data.Stride
  $bytes = $stride * $SH
  $buf = New-Object byte[] $bytes
  [System.Runtime.InteropServices.Marshal]::Copy($data.Scan0, $buf, 0, $bytes)
  $bmpSmall.UnlockBits($data)

  if ($prevBytes -ne $null -and $stride -eq $prevStride) {
    $diff = 0
    $minX = $SW; $minY = $SH; $maxX = 0; $maxY = 0
    for ($y = 0; $y -lt $SH; $y += 2) {
      $base = $y * $stride
      for ($x = 0; $x -lt $SW; $x += 2) {
        $i = $base + $x * 4
        $dr = [Math]::Abs([int]$buf[$i] - [int]$prevBytes[$i])
        $dg = [Math]::Abs([int]$buf[$i+1] - [int]$prevBytes[$i+1])
        $db = [Math]::Abs([int]$buf[$i+2] - [int]$prevBytes[$i+2])
        if (($dr + $dg + $db) -gt $Threshold) {
          $diff++
          if ($x -lt $minX) { $minX = $x }
          if ($x -gt $maxX) { $maxX = $x }
          if ($y -lt $minY) { $minY = $y }
          if ($y -gt $maxY) { $maxY = $y }
        }
      }
    }

    if ($diff -gt $MinChangedCells) {
      $totalEvents++
      $totalCells = [int](($SW/2) * ($SH/2))
      $pct = [Math]::Round($diff * 100.0 / $totalCells, 3)
      $rec = [ordered]@{
        ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
        frame = $frame
        changed = $diff
        pct = $pct
        x = [int]($minX * $DownScale)
        y = [int]($minY * $DownScale)
        w = [int](($maxX - $minX + 1) * $DownScale)
        h = [int](($maxY - $minY + 1) * $DownScale)
      }
      ($rec | ConvertTo-Json -Compress) | Add-Content -Path $OutFile -Encoding UTF8
    }
  }

  $prevBytes = $buf
  $prevStride = $stride
  $frame++
  Start-Sleep -Milliseconds $interval
}

$gFull.Dispose(); $gSmall.Dispose()
$bmpFull.Dispose(); $bmpSmall.Dispose()

$endRec = [ordered]@{ meta='end'; ts=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds(); frames=$frame; events=$totalEvents }
($endRec | ConvertTo-Json -Compress) | Add-Content -Path $OutFile -Encoding UTF8
