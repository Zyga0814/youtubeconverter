from pathlib import Path
import shutil
import zipfile

root = Path(r"C:\Users\PC\Documents\Convert youtube video to mp3")
dist = root / "dist"
bundle_dir = dist / "portable_bundle"
zip_path = dist / "YouTubeConverter_portable.zip"
exe_path = dist / "YouTubeConverter.exe"
export_dir = root / "export mp3 or mp4"
ffmpeg_dir = Path(r"C:\Users\PC\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin")

if bundle_dir.exists():
    shutil.rmtree(bundle_dir)
bundle_dir.mkdir(parents=True, exist_ok=True)

if exe_path.exists():
    shutil.copy2(exe_path, bundle_dir / exe_path.name)
else:
    raise FileNotFoundError(f"Missing EXE: {exe_path}")

for name in ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]:
    src = ffmpeg_dir / name
    if src.exists():
        shutil.copy2(src, bundle_dir / name)
    else:
        raise FileNotFoundError(f"Missing FFmpeg binary: {src}")

if export_dir.exists():
    target_export = bundle_dir / export_dir.name
    shutil.copytree(export_dir, target_export, dirs_exist_ok=True)

if zip_path.exists():
    zip_path.unlink()

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for path in bundle_dir.iterdir():
        if path.is_file():
            zf.write(path, arcname=path.name)
        elif path.is_dir():
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, arcname=file_path.relative_to(bundle_dir))

print(f"Created bundle directory: {bundle_dir}")
print(f"Created portable archive: {zip_path}")
