# converter class for converting audio, image, video and document files
#
# Current implementation status:
# - Audio: working for mp3, wav, flac and ogg.
# - Image: partially working for static raster images supported by Pillow.
# - Documents: not working as a real converter yet. python-docx only handles
#   .docx files and cannot convert arbitrary office/document formats.
# - Video: not implemented yet. The UI currently calls convert_video(), but
#   this class does not define that method.
#
# Project constraint:
# - Prefer Python-package based conversion backends.
# - Avoid requiring users to have FFmpeg installed as a system binary.
# - For video, this likely means using a packaged media backend such as PyAV,
#   with the caveat that PyAV still uses FFmpeg libraries under the hood.

# ----------
# imports

import threading
from io import BytesIO
from pathlib import Path

import lameenc
import miniaudio
import numpy as np
import soundfile as sf
from docx import Document
from PIL import Image

# ----------
# main class
# it centralizes the conversion API used by the Streamlit interface.
#
# Important:
# This class should not pretend every format pair is supported. Each converter
# method should validate the input/output pair and raise a clear ValueError for
# unsupported conversions.


class FileConverter:
    def __init__(self, input_file, input_ext: str, output_ext: str):
        self.input_file = input_file
        self.input_ext = input_ext.lower().lstrip(".")
        self.output_ext = output_ext.lower().lstrip(".")

    # helper method to get the soundfile-compatible audio container name
    # for non-MP3 output formats.
    #
    # MP3 is intentionally not included here because it is encoded with lameenc.
    @staticmethod
    def _audio_format(ext: str) -> str:
        formats = {
            "wav": "WAV",
            "flac": "FLAC",
            "ogg": "OGG",
        }

        if ext not in formats:
            raise ValueError(f"Unsupported audio format: {ext}")

        return formats[ext]

    # helper method to get the Pillow-compatible image format name.
    #
    # Pending:
    # - add "jpg" as an alias for "jpeg";
    # - handle transparency when converting RGBA/LA/P images to JPEG;
    # - decide whether animated formats should be supported or rejected.
    @staticmethod
    def _image_format(ext: str) -> str:
        formats = {
            "png": "PNG",
            "jpg": "JPEG",
            "jpeg": "JPEG",
            "webp": "WEBP",
            "avif": "AVIF",
        }

        if ext not in formats:
            raise ValueError(f"Unsupported image format: {ext}")

        return formats[ext]

    # document format labels.
    #
    # Current problem:
    # This mapping is not enough to convert documents. Unlike images/audio,
    # office/document formats do not share one simple encoder API.
    #
    # python-docx only supports .docx files. It does not convert .docx to PDF,
    # XLSX, PPTX, ODT, MD, TXT, etc.
    #
    # Recommended next step:
    # Replace convert_office() with format-pair specific document handlers:
    # - docx <-> txt/md basics through python-docx
    # - xlsx/csv through openpyxl + csv
    # - ods through odfpy, if kept
    # - pdf operations through PyMuPDF/pypdf
    # - optional pandoc backend only if bundled/available
    @staticmethod
    def _office_format(ext: str) -> str:
        formats = {
            "doc": "DOC",
            "docx": "DOCX",
            "pdf": "PDF",
            "xls": "XLS",
            "ods": "ODS",
            "odf": "ODF",
            "ppt": "PPT",
            "pptx": "PPTX",
            "odt": "ODT",
        }

        if ext not in formats:
            raise ValueError(f"Unsupported document format: {ext}")

        return formats[ext]

    # video format labels.
    #
    # Current problem:
    # This mapping is unused because convert_video() is not implemented.
    #
    # Recommended direction:
    # - If "no FFmpeg" means no system-level ffmpeg executable, evaluate PyAV.
    # - If "no FFmpeg at all" means no FFmpeg libraries either, full MP4/MKV/
    #   MOV/AVI/WebM transcoding should be considered out of scope.
    @staticmethod
    def _video_format(ext: str) -> str:
        formats = {
            "mp4": "MP4",
            "mkv": "MKV",
            "webm": "WebM",
            "avi": "AVI",
            "mov": "MOV",
        }

        if ext not in formats:
            raise ValueError(f"Unsupported video format: {ext}")

        return formats[ext]

    # ----------
    # audio

    def _decode_audio(self):
        """
        Decode the input file to int16 PCM samples plus sample_rate.

        MP3 is decoded with miniaudio.

        WAV, FLAC and OGG are read directly with soundfile/libsndfile. This
        keeps the audio path independent from FFmpeg.

        Pending:
        - call self.input_file.seek(0) before read() to support repeated reads;
        - validate self.input_ext before decoding;
        - preserve or expose channel count and duration metadata if needed.
        """
        input_bytes = self.input_file.read()

        if self.input_ext == "mp3":
            decoded = miniaudio.decode(
                input_bytes, output_format=miniaudio.SampleFormat.SIGNED16
            )
            samples = np.frombuffer(decoded.samples, dtype=np.int16)
            if decoded.nchannels > 1:
                samples = samples.reshape(-1, decoded.nchannels)
            return samples, decoded.sample_rate

        samples, sample_rate = sf.read(BytesIO(input_bytes), dtype="int16")
        return samples, sample_rate

    def _write_audio(self, samples, sample_rate):
        """
        Write decoded PCM samples to WAV, FLAC or OGG.

        OGG is written in a separate thread with a larger stack because of a
        known libsndfile/Vorbis issue on Windows: long OGG writes can overflow
        the default Windows thread stack and crash the process without a Python
        traceback.

        Pending:
        - confirm whether the workaround should be Windows-only;
        - add tests for long OGG exports.
        """
        self.input_file.seek(0)
        audio_format = self._audio_format(self.output_ext)
        output = BytesIO()

        if self.output_ext != "ogg":
            sf.write(output, samples, sample_rate, format=audio_format)
            output.seek(0)
            return output

        errors = []

        def _run():
            try:
                sf.write(output, samples, sample_rate, format=audio_format)
            except Exception as exc:
                errors.append(exc)

        previous_stack_size = threading.stack_size()
        threading.stack_size(16 * 1024 * 1024)  # 16 MB
        try:
            t = threading.Thread(target=_run)
            t.start()
            t.join()
        finally:
            threading.stack_size(previous_stack_size)

        if errors:
            raise errors[0]

        output.seek(0)
        return output

    def _encode_mp3(self, samples, sample_rate):
        """
        Encode int16 PCM samples to MP3 using lameenc.

        Pending:
        - expose bitrate/quality as user options later;
        - validate channel layout for uncommon audio inputs.
        """
        if samples.dtype != np.int16:
            samples = samples.astype(np.int16)

        nchannels = samples.shape[1] if samples.ndim > 1 else 1

        encoder = lameenc.Encoder()
        encoder.set_in_sample_rate(sample_rate)
        encoder.set_channels(nchannels)
        encoder.set_quality(2)
        encoder.set_bit_rate(192)

        output = BytesIO()
        output.write(encoder.encode(samples.tobytes()))
        output.write(encoder.flush())
        output.seek(0)
        return output

    def convert_audio(self):
        """
        Convert supported audio formats.

        Supported:
        - mp3 -> wav/flac/ogg
        - wav/flac/ogg -> mp3
        - wav/flac/ogg -> wav/flac/ogg

        Unsupported formats should be rejected before decoding.
        """
        samples, sample_rate = self._decode_audio()

        if self.output_ext == "mp3":
            return self._encode_mp3(samples, sample_rate)

        return self._write_audio(samples, sample_rate)

    def convert_image(self):
        """
        Convert static raster images with Pillow.

        Current behavior:
        - converts JPEG output to RGB;
        - writes the requested output format to BytesIO.

        Pending:
        - add jpg/jpeg alias support;
        - flatten transparency safely before JPEG output;
        - decide whether to reject or support animated images;
        - preserve metadata intentionally, not accidentally.
        """
        self.input_file.seek(0)
        img = Image.open(self.input_file)
        if self.output_ext == "jpg" or self.output_ext == "jpeg":
            img = img.convert("RGB")
        output = BytesIO()
        img.save(output, format=self._image_format(self.output_ext))
        output.seek(0)
        return output

    # ----------
    # documents
    #
    # Current status:
    # Broken as a converter.
    #
    # The old comment saying "Document not imported" is outdated. Document is
    # imported now. The real bug is that python-docx is not a general document
    # conversion engine and Document.save() does not accept a format argument.
    #
    # Recommended:
    # Replace this method with a dispatcher that handles explicit conversion
    # pairs. Until then, this method should raise NotImplementedError instead
    # of pretending to convert documents.

    def convert_office(self):
        self.input_file.seek(0)
        doc = Document(self.input_file)
        output = BytesIO()
        doc.save(output, format=self._office_format(self.output_ext))
        output.seek(0)
        return output

    # ----------
    # video
    #
    # Current status:
    # Not implemented.
    #
    # The Streamlit UI currently calls convert_video(), so this method should
    # either be implemented or the UI should disable video conversion.
    #
    # Recommended:
    # - choose a backend first;
    # - PyAV is the realistic option if the requirement is "do not require the
    #   ffmpeg executable installed on the user's machine";
    # - if FFmpeg libraries are also forbidden, full video transcoding should
    #   be marked unsupported.
