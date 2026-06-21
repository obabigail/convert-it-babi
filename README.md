# convert-it-babi

A simple Python script with Streamlit to convert different types of files.

## What it does

convert-it-babi is a Streamlit app for converting audio, image, video and office files, with no dependency on FFmpeg or other external binaries - conversions are done entirely through Python libraries (`miniaudio`, `soundfile`, `lameenc`, `Pillow`, `python-docx`).

## Status

| Type     | Status      | Formats               |
|----------|-------------|------------------------|
| Audio    | Working     | mp3, wav, flac, ogg   |
| Image    | In progress | png, jpg, webp, avif  |
| Document | In progress | -                      |
| Video    | Not started | -                      |

## Installation

```bash
pip install streamlit soundfile miniaudio lameenc numpy pillow python-docx
```

## Usage

```bash
streamlit run main.py
```

Pick a file type, choose the input and output format, upload a file, and convert.

## Notes

- Audio conversion decodes MP3 via `miniaudio` and reads WAV/FLAC/OGG natively via `soundfile`; encoding follows the same split: `lameenc` for MP3, `soundfile` for everything else.
- OGG export runs in a dedicated thread with a 16 MB stack to work around a known libsndfile bug on Windows, where the Vorbis encoder can overflow a thread's default 1 MB stack on long audio and crash the process with no traceback. See [bastibe/python-soundfile#396](https://github.com/bastibe/python-soundfile/issues/396).
