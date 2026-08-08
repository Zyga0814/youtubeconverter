# YouTube to MP3/MP4 Converter

This project downloads a YouTube video and converts it to either MP3 or MP4.

## Requirements

1. Install Python 3.8+.
2. Install the Python package:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Install FFmpeg and add it to your PATH.
   - This is required for audio conversion and video merging.

## Usage

### Graphical interface
Run the app with:
```bash
python converter.py
```

Then paste a YouTube URL, choose MP3 or MP4, and click Convert.

### Command line
Convert to MP3:
```bash
python converter.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --format mp3
```

Convert to MP4:
```bash
python converter.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --format mp4
```

Outputs will be saved inside the folder named `export mp3 or mp4`.
