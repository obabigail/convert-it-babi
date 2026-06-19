# converter class for converting audio, image, video and office suite files

# ----------
# imports

import wave
from io import BytesIO
from pathlib import Path

import lameenc
import miniaudio
import numpy as np
import soundfile as sf
from PIL import Image
from scipy.io import wavfile

# ----------
# main class
# it will encompass the conversion logic for all supported file types


class FileConverter:
    def __init__(self, input_file, input_ext: str, output_ext: str):
        self.input_file = input_file
        self.input_ext = input_ext.lower().lstrip(".")
        self.output_ext = output_ext.lower().lstrip(".")

    # helper method to get the soundfile format for the output file
    @staticmethod
    def _soundfile_format(ext: str) -> str:
        formats = {
            "wav": "WAV",
            "flac": "FLAC",
            "ogg": "OGG",
        }

        if ext not in formats:
            raise ValueError(f"Formato de áudio não suportado sem FFmpeg: {ext}")

        return formats[ext]

    def convert_image(self):
        # open the image file
        img = Image.open(self.input_ext)

        # convert the image to RGB mode
        img = img.convert("RGB")

        # save the converted image to the output path
        img.save(self.output_ext)

    def convert_office(self):
        # open the office file
        doc = Document(self.input_ext)

        # convert the office file to the output path
        doc.save(self.output_ext)

    def convert_audio(self):
        """
        the objective is to not use ffmpeg, since it requires user installation
        that makes the function more complex, since it requires different logic
        and libraries for different audio formats:
            MP3 to other formats: miniaudio with numpy
            Other formats to MP3: lameenc with wave
            else: soundfile with numpy
        """

        # read the input file into memory
        input_bytes = self.input_file.read()
        output = BytesIO()

        if self.input_ext.endswith("mp3"):
            # decode the MP3 file
            decoded = miniaudio.decode(
                input_bytes,
                output_format=miniaudio.SampleFormat.SIGNED16,
            )

            # convert the decoded samples to the output format
            samples = np.frombuffer(decoded.samples, dtype=np.int16)

            if decoded.nchannels > 1:
                samples = samples.reshape(-1, decoded.nchannels)

            # save the samples to the output path
            sf.write(
                output,
                samples,
                decoded.sample_rate,
                format=self._soundfile_format(self.output_ext),
            )

            output.seek(0)
            return output

        # elif self.output_ext.endswith(".mp3"):
        #     # open the file and extract properties
        #     with wave.open(output, "rb") as audio_file:
        #         sample_rate = audio_file.getframerate()
        #         nchannels = audio_file.getnchannels()
        #         samples = audio_file.readframes(audio_file.getnframes())

        #     # initialize the MP3 encoder
        #     mp3_encoder = lameenc.Encoder()
        #     mp3_encoder.set_sample_rate(sample_rate)
        #     mp3_encoder.set_channels(nchannels)
        #     mp3_encoder.set_quality(2)

        #     # process and stream data to MP3 file
        #     with open(self.output_ext, "wb") as mp3_file:
        #         mp3_file.write(mp3_encoder.encode(samples))
        #         mp3_file.write(mp3_encoder.flush())

        else:
            # # read the audio file into a numpy array
            # data, sample_rate = sf.read(self.input_ext)

            # # save the data to the output path
            # sf.write(self.output_ext, data, sample_rate)
            raise NotImplementedError(f"Unsupported output format: {self.output_ext}")
