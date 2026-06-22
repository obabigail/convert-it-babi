# converter class for converting audio, image, video and office suite files

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
# it will encompass the conversion logic for all supported file types


class FileConverter:
    def __init__(self, input_file, input_ext: str, output_ext: str):
        self.input_file = input_file
        self.input_ext = input_ext.lower().lstrip(".")
        self.output_ext = output_ext.lower().lstrip(".")

    # helper method to get the audio format for the output file
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

    # helper method to get the image format for the output file
    @staticmethod
    def _image_format(ext: str) -> str:
        formats = {
            "png": "PNG",
            "jpeg": "JPEG",
            "webp": "WEBP",
            "avif": "AVIF",
        }

        if ext not in formats:
            raise ValueError(f"Unsupported image format: {ext}")

        return formats[ext]

    # helper method to get the office format for the output file
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
            raise ValueError(f"Unsupported image format: {ext}")

        return formats[ext]

    # ----------
    # audio

    def _decode_audio(self):
        """
        Decode the input file to int16 PCM + sample_rate.

        MP3 goes through miniaudio because libsndfile (used by soundfile)
        doesn't decode MP3 reliably in the wheels distributed via pip.
        WAV, FLAC and OGG are read directly by soundfile, which already
        knows how to open those containers natively - no need for the
        wave module.
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
        Write the decoded samples to the output format (WAV/FLAC/OGG).

        OGG runs in a separate thread with a larger stack because of a
        known libsndfile bug on Windows: the Vorbis encoder overflows a
        Windows thread's default 1 MB stack when writing audio with many
        frames, crashing the whole process with no traceback.
        Source: github.com/bastibe/python-soundfile/issues/396
        """
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
        samples, sample_rate = self._decode_audio()

        if self.output_ext == "mp3":
            return self._encode_mp3(samples, sample_rate)

        return self._write_audio(samples, sample_rate)

    def convert_image(self):
        self.input_file.seek(0)
        img = Image.open(self.input_file)
        if self.output_ext == "jpeg":
            img = img.convert("RGB")
        output = BytesIO()
        img.save(output, format=self._image_format(self.output_ext))
        output.seek(0)
        return output

    # ----------
    # office - still has the original bug (Document not imported), not
    # touched in this round

    def convert_office(self):
        doc = Document(self.input_file)
        output = BytesIO()
        doc.save(output, format=self._office_format(self.output_ext))
        output.seek(0)
        return output
