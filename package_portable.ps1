$root = 'C:\Users\PC\Documents\Convert youtube video to mp3'
$dist = Join-Path $root 'dist'
$bundle = Join-Path $dist 'portable_bundle'
$zip = Join-Path $dist 'YouTubeConverter_portable.zip'
$exe = Join-Path $dist 'YouTubeConverter.exe'
$export = Join-Path $root 'export mp3 or mp4'
$ffmpegDir = 'C:\Users\PC\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin'

if (Test-Path $bundle) { Remove-Item $bundle -Recurse -Force }
New-Item -ItemType Directory -Force -Path $bundle | Out-Null
Copy-Item $exe -Destination $bundle
Copy-Item (Join-Path $ffmpegDir 'ffmpeg.exe') -Destination $bundle
Copy-Item (Join-Path $ffmpegDir 'ffprobe.exe') -Destination $bundle
Copy-Item (Join-Path $ffmpegDir 'ffplay.exe') -Destination $bundle

if (Test-Path $export) {
    Copy-Item $export -Destination (Join-Path $bundle 'export mp3 or mp4') -Recurse
}

if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $bundle '*') -DestinationPath $zip -Force

Write-Host "Created bundle: $bundle"
Write-Host "Created archive: $zip"
