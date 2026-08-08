#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import END, StringVar, Tk, ttk
from tkinter import filedialog


def resolve_output_root(output_root: str | None) -> Path:
    if output_root:
        return Path(output_root).expanduser().resolve()
    return Path(__file__).resolve().parent / "export mp3 or mp4"


def build_output_dir(output_root: str | None, fmt: str) -> Path:
    output_dir = resolve_output_root(output_root) / fmt
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def find_latest_file(folder: Path) -> Path | None:
    files = [path for path in folder.iterdir() if path.is_file()]
    if not files:
        return None
    return max(files, key=lambda path: path.stat().st_mtime)


def find_ffmpeg_path(ffmpeg_dir: str | None = None) -> tuple[str | None, str | None]:
    if ffmpeg_dir:
        root = Path(ffmpeg_dir).expanduser().resolve()
        ffmpeg_path = root / "ffmpeg.exe"
        ffprobe_path = root / "ffprobe.exe"
        if ffmpeg_path.exists() and ffprobe_path.exists():
            return str(ffmpeg_path), str(ffprobe_path)
        if ffmpeg_path.exists():
            return str(ffmpeg_path), None
        if ffprobe_path.exists():
            return None, str(ffprobe_path)

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg and ffprobe:
        return ffmpeg, ffprobe

    candidate_roots = [
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "ffmpeg" / "bin",
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "ffmpeg" / "bin",
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "FFmpeg" / "bin",
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "FFmpeg" / "bin",
        Path.home() / "ffmpeg" / "bin",
        Path.home() / "Downloads",
        Path(__file__).resolve().parent / "ffmpeg" / "bin",
        Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-8.1.2-full_build" / "bin",
    ]
    for root in candidate_roots:
        ffmpeg_path = root / "ffmpeg.exe"
        ffprobe_path = root / "ffprobe.exe"
        if ffmpeg_path.exists() and ffprobe_path.exists():
            return str(ffmpeg_path), str(ffprobe_path)

    for root in candidate_roots:
        if root.exists():
            for path in root.rglob("ffmpeg.exe"):
                ffmpeg_path = path
                ffprobe_path = path.with_name("ffprobe.exe")
                if ffprobe_path.exists():
                    return str(ffmpeg_path), str(ffprobe_path)
    return None, None


def resolve_ffmpeg_options(ffmpeg_path: str | None, ffprobe_path: str | None) -> dict:
    options = {}
    if ffmpeg_path:
        options["ffmpeg_location"] = ffmpeg_path
    if ffprobe_path:
        options["ffprobe_location"] = ffprobe_path
    return options


def install_ffmpeg() -> tuple[bool, str]:
    for candidate in ["winget", "choco", "scoop"]:
        if shutil.which(candidate):
            if candidate == "winget":
                command = [candidate, "install", "--id", "Gyan.dev.FFmpeg", "-e"]
            elif candidate == "choco":
                command = [candidate, "install", "ffmpeg", "-y"]
            else:
                command = [candidate, "bucket", "add", "main"]
                subprocess.run(command, check=False, capture_output=True, text=True)
                command = [candidate, "install", "ffmpeg"]
            try:
                result = subprocess.run(command, check=False, capture_output=True, text=True)
                if result.returncode == 0:
                    return True, "FFmpeg installation completed."
                output = (result.stdout + result.stderr).strip()
                if output:
                    return False, output
            except OSError as exc:
                return False, str(exc)
    return False, "No supported package manager was found. Please install FFmpeg manually from https://www.ffmpeg.org/download.html"


def download_youtube(url: str, fmt: str, output_root: str | None, status_callback=None, ffmpeg_dir: str | None = None) -> None:
    try:
        from yt_dlp import YoutubeDL
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency. Install it with: python -m pip install -r requirements.txt"
        ) from exc

    output_dir = build_output_dir(output_root, fmt)
    if status_callback:
        status_callback(f"Preparing download folder: {output_dir}")

    ffmpeg_path, ffprobe_path = find_ffmpeg_path(ffmpeg_dir)
    if not (ffmpeg_path and ffprobe_path):
        raise RuntimeError(
            "FFmpeg and FFprobe were not found. Install FFmpeg and make sure ffmpeg.exe and ffprobe.exe are available, or choose the folder that contains them in the app."
        )

    if fmt == "mp3":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "0",
                }
            ],
            "quiet": False,
            "noplaylist": True,
            "progress_hooks": [lambda info: status_callback and status_callback(_format_progress(info))],
            **resolve_ffmpeg_options(ffmpeg_path, ffprobe_path),
        }
    else:
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "quiet": False,
            "noplaylist": True,
            "progress_hooks": [lambda info: status_callback and status_callback(_format_progress(info))],
            **resolve_ffmpeg_options(ffmpeg_path, ffprobe_path),
        }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    if status_callback:
        status_callback(f"Done. Files are in: {output_dir}")


def _format_progress(info: dict) -> str:
    if info.get("_percent_str"):
        return f"Downloading: {info['_percent_str']}"
    if info.get("status") == "finished":
        return "Finishing conversion..."
    return f"Status: {info.get('status', 'working')}"


class YouTubeConverterApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("YouTube to MP3/MP4 Converter")
        self.root.geometry("900x560")
        self.root.minsize(860, 520)
        self.root.resizable(True, True)

        self.url_var = StringVar(value="")
        self.format_var = StringVar(value="mp3")
        self.output_var = StringVar(value=str(resolve_output_root(None)))
        self.status_var = StringVar(value="Paste a YouTube link and click Convert")

        header = ttk.Label(root, text="YouTube to MP3/MP4 Converter", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w", padx=20, pady=(18, 8))
        ttk.Label(root, text="Paste your YouTube URL, choose a format, and start downloading.", wraplength=860).pack(anchor="w", padx=20, pady=(0, 10))

        url_frame = ttk.Frame(root)
        url_frame.pack(fill="x", padx=20, pady=6)
        ttk.Label(url_frame, text="YouTube URL").pack(anchor="w")
        ttk.Entry(url_frame, textvariable=self.url_var).pack(fill="x", pady=4)

        options_frame = ttk.Frame(root)
        options_frame.pack(fill="x", padx=20, pady=8)
        ttk.Label(options_frame, text="Output format").pack(anchor="w")
        ttk.Combobox(options_frame, textvariable=self.format_var, values=["mp3", "mp4"], state="readonly", width=12).pack(anchor="w", pady=4)

        output_frame = ttk.Frame(root)
        output_frame.pack(fill="x", padx=20, pady=8)
        ttk.Label(output_frame, text="Output folder").pack(anchor="w")
        ttk.Entry(output_frame, textvariable=self.output_var).pack(fill="x", side="left", expand=True, pady=4)
        ttk.Button(output_frame, text="Browse", command=self.browse_output).pack(side="left", padx=(10, 0), pady=4)

        ffmpeg_frame = ttk.Frame(root)
        ffmpeg_frame.pack(fill="x", padx=20, pady=8)
        ttk.Label(ffmpeg_frame, text="FFmpeg folder").pack(anchor="w")
        self.ffmpeg_dir_var = StringVar(value="")
        ttk.Entry(ffmpeg_frame, textvariable=self.ffmpeg_dir_var).pack(fill="x", side="left", expand=True, pady=4)
        ttk.Button(ffmpeg_frame, text="Browse", command=self.browse_ffmpeg_folder).pack(side="left", padx=(10, 0), pady=4)
        ttk.Button(ffmpeg_frame, text="Install FFmpeg", command=self.install_ffmpeg_from_ui).pack(side="left", padx=(10, 0), pady=4)

        button_frame = ttk.Frame(root)
        button_frame.pack(fill="x", padx=20, pady=12)
        ttk.Button(button_frame, text="Convert", command=self.start_conversion).pack(side="left")
        ttk.Button(button_frame, text="Open folder", command=self.open_output_folder).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Open latest file", command=self.open_latest_file).pack(side="left")
        ttk.Button(button_frame, text="Exit", command=root.destroy).pack(side="left", padx=10)

        ttk.Label(root, textvariable=self.status_var, wraplength=860, justify="left").pack(anchor="w", padx=20, pady=(6, 4))
        self.log_box = ttk.Frame(root)
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(4, 12))
        self.log_text = tk.Text(self.log_box, height=12, wrap="word")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.insert(END, "Ready.\n")

        self.processing = False

    def browse_output(self) -> None:
        folder = filedialog.askdirectory(initialdir=str(resolve_output_root(None)))
        if folder:
            self.output_var.set(folder)

    def browse_ffmpeg_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select FFmpeg folder")
        if folder:
            self.ffmpeg_dir_var.set(folder)

    def install_ffmpeg_from_ui(self) -> None:
        self.set_status("Installing FFmpeg... this may take a moment")
        self.root.update_idletasks()
        success, message = install_ffmpeg()
        if success:
            self.set_status(message)
            self.log_text.insert(END, message + "\n")
        else:
            self.set_status(message)
            self.log_text.insert(END, message + "\n")

    def open_output_folder(self) -> None:
        folder = self.output_var.get()
        if folder:
            os.startfile(folder) if hasattr(os, "startfile") else os.system(f"xdg-open {folder}")

    def open_latest_file(self) -> None:
        folder = Path(self.output_var.get()) / self.format_var.get()
        if not folder.exists():
            self.set_status("No converted file found in that folder yet")
            return
        latest = find_latest_file(folder)
        if latest:
            os.startfile(str(latest)) if hasattr(os, "startfile") else os.system(f"xdg-open {latest}")
            self.set_status(f"Opened: {latest.name}")
        else:
            self.set_status("No converted file found in that folder yet")

    def start_conversion(self) -> None:
        url = self.url_var.get().strip()
        if not url.startswith(("http://", "https://")):
            self.set_status("Please enter a valid YouTube URL")
            return
        if self.processing:
            return

        self.processing = True
        self.set_status("Starting conversion...")
        self.log_text.delete("1.0", END)
        self.log_text.insert(END, f"URL: {url}\n")
        self.log_text.insert(END, f"Format: {self.format_var.get()}\n")
        self.root.after(0, lambda: threading.Thread(target=self._run_conversion, args=(url,), daemon=True).start())

    def _run_conversion(self, url: str) -> None:
        try:
            download_youtube(
                url,
                self.format_var.get(),
                self.output_var.get(),
                status_callback=self.update_status,
                ffmpeg_dir=self.ffmpeg_dir_var.get(),
            )
        except Exception as exc:  # noqa: BLE001
            self.update_status(f"Error: {exc}")
        finally:
            self.root.after(0, self.finish_conversion)

    def update_status(self, message: str) -> None:
        if self.root.winfo_exists():
            self.root.after(0, lambda: self._apply_status(message))

    def _apply_status(self, message: str) -> None:
        self.status_var.set(message)
        self.log_text.insert(END, message + "\n")
        self.log_text.see(END)

    def finish_conversion(self) -> None:
        self.processing = False
        self.set_status("Finished. Use Open latest file to play it.")

    def set_status(self, message: str) -> None:
        self.status_var.set(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a YouTube video to MP3 or MP4")
    parser.add_argument("--url", help="The YouTube video URL")
    parser.add_argument(
        "--format",
        choices=["mp3", "mp4"],
        default="mp3",
        help="Choose the output format",
    )
    parser.add_argument(
        "--output-root",
        default=str(resolve_output_root(None)),
        help="Where to save converted files",
    )
    args = parser.parse_args()

    if args.url:
        if not args.url.startswith(("http://", "https://")):
            print("Please provide a valid URL starting with http:// or https://")
            return 2
        download_youtube(args.url, args.format, args.output_root)
        return 0

    root = tk.Tk()
    app = YouTubeConverterApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
