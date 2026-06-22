# convert-it-babi

A simple Streamlit app for converting audio, image, video and document files.

The current goal is to keep conversions self-contained in Python packages whenever possible, avoiding a required system-level FFmpeg installation for better compatibility on devices where FFmpeg is not installed.

## What it currently does

`convert-it-babi` is a Streamlit app that currently supports:

* audio conversion between `mp3`, `wav`, `flac` and `ogg`;
* basic image conversion between `png`, `jpeg`, `webp` and `avif`;
* document and video UI placeholders, not working conversion logic yet.

## Current status

| Type     | Status      | Formats shown in UI                                                    | Notes                                                                                                                                                |
| -------- | ----------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Audio    | Working     | `mp3`, `wav`, `flac`, `ogg`                                            | MP3 is decoded with `miniaudio` and encoded with `lameenc`; WAV/FLAC/OGG are handled with `soundfile`.                                               |
| Image    | Partial     | `png`, `jpeg`, `webp`, `avif`                                          | Basic raster conversion works through Pillow, but transparency, animated images, metadata, ICC profiles and `jpg` alias handling still need cleanup. |
| Document | Broken      | `docx`, `xlsx`, `pptx`, `pdf`, `ods`, `odf`, `odt`, `tex`, `txt`, `md` | The current implementation uses `python-docx`, which only handles `.docx` documents. It cannot convert between arbitrary document formats.           |
| Video    | Not started | `mp4`, `mkv`, `mov`, `avi`, `webm`                                     | The UI calls `convert_video()`, but this method does not exist yet.                                                                                  |

## Installation

```bash
pip install streamlit soundfile miniaudio lameenc numpy pillow python-docx
```

Current dependencies cover only audio, basic images and `.docx` loading/saving experiments.

Document and video conversion will require additional libraries depending on the chosen strategy.

## Usage

```bash
streamlit run main.py
```

Pick a file type, choose the input and output format, upload a file, then convert.

## What was fixed recently

* Audio conversion flow was cleaned up.
* MP3 decoding now uses `miniaudio`.
* MP3 encoding now uses `lameenc`.
* WAV, FLAC and OGG are read/written through `soundfile`.
* OGG export runs inside a dedicated thread with a larger stack to avoid a known Windows crash caused by libsndfile/Vorbis stack overflow on long files.
* Image conversion now uses Pillow directly.
* `Document` from `python-docx` is now imported, so the previous “Document not imported” bug is no longer accurate.

## Known bugs and current errors

### Document converter

The current `convert_office()` implementation is broken.

Current code:

```python
doc = Document(self.input_file)
doc.save(output, format=self._office_format(self.output_ext))
```

Problems:

* `python-docx` only opens Word `.docx` files.
* It does not open `pdf`, `xlsx`, `pptx`, `ods`, `odf`, `odt`, `tex`, `txt` or `md`.
* `Document.save()` does not accept a `format=` argument.
* `_office_format()` does not include all formats listed in the UI, such as `xlsx`, `tex`, `txt` and `md`.
* The UI allows many document pairs that the backend cannot support.
* A generic “office converter” method is not enough; document conversion needs different engines per format family.

### Video converter

The video converter is not implemented.

Problems:

* `_render_video_converter()` calls `converter.convert_video()`.
* `FileConverter` does not define `convert_video()`.
* `_video_format()` exists but is unused.
* No video decoding/encoding library is imported.
* The video UI currently suggests support that does not exist.

### Image converter

The image converter is only partially safe.

Pending issues:

* `jpg` is not accepted as an alias for `jpeg`.
* PNG/WebP/AVIF images with alpha converted to JPEG may lose transparency incorrectly.
* Animated WebP/AVIF files are not handled intentionally.
* Metadata, EXIF orientation and ICC profiles are not preserved explicitly.
* AVIF support depends on the installed Pillow build.

### Streamlit UI

Small UI issues:

* Audio error message says `Failed to convert image`.
* Video uploader label says `Upload Document`.
* Document download MIME type uses `document/{output_type}`, which is not a reliable MIME type.
* The UI should disable unsupported conversion pairs instead of showing all combinations.

## Suggested direction for document conversion

Do not keep a single generic `convert_office()` method. Split document conversion by family.

Recommended internal structure:

```text
convert_document()
├── convert_text_document()      # txt, md, maybe tex
├── convert_docx_document()      # docx-specific operations
├── convert_spreadsheet()        # xlsx/ods/csv-like workflows
├── convert_presentation()       # pptx-specific workflows
└── convert_pdf_document()       # pdf extraction/rendering/splitting/merging
```

Practical no-system-binary options:

### Text and markup

Good first targets:

* `txt` to `md`
* `md` to `txt`
* basic `md` to `html`
* basic `txt` to `docx`
* basic `md` to `docx`

Possible libraries:

* standard Python file handling for `txt`;
* `markdown` or `mistune` for Markdown to HTML;
* `python-docx` for generating `.docx`.

Limitations:

* high-fidelity conversion from `.docx` to `.md` is not trivial;
* `.tex` support should be treated as plain text unless a real parser is added;
* PDF generation from HTML/Markdown usually requires an HTML/CSS rendering engine, which may add heavy dependencies.

### DOCX

Reasonable first targets:

* `docx` to `txt`
* `docx` to simple `md`
* `txt` to `docx`
* `md` to basic `docx`

Possible library:

* `python-docx`

Limitations:

* not a general document converter;
* does not convert `.docx` directly to `.pdf`;
* does not handle old `.doc`;
* complex formatting, headers, footnotes, comments and tracked changes may not round-trip cleanly.

### XLSX / spreadsheets

Reasonable first targets:

* `xlsx` to `csv`
* `csv` to `xlsx`
* simple `xlsx` to `txt`

Possible libraries:

* `openpyxl` for `.xlsx`;
* `csv` from the standard library;
* `odfpy` for OpenDocument formats, if ODS support is kept.

Limitations:

* formulas, charts, macros and pivot tables need explicit decisions;
* `.xls` is a different legacy format and should not be treated as `.xlsx`.

### PPTX

Reasonable first targets:

* `pptx` to text extraction;
* image extraction from slides;
* simple `txt` or `md` to generated `pptx`.

Possible library:

* `python-pptx`

Limitations:

* not a PPTX-to-PDF converter;
* not a full PowerPoint rendering engine;
* preserving slide layout during conversion is hard without PowerPoint/LibreOffice-like rendering.

### PDF

Reasonable first targets:

* PDF to text;
* PDF to images;
* images to PDF;
* merge/split PDFs.

Possible libraries:

* `PyMuPDF`;
* `pypdf`.

Limitations:

* PDF to editable DOCX/PPTX/XLSX is a hard problem;
* scanned PDFs require OCR;
* preserving layout is difficult.

### Pandoc option

`pypandoc` can cover many document conversions, but it depends on Pandoc. That conflicts with the “no external binaries installed on the system” goal unless the project accepts bundling Pandoc through a package such as `pypandoc_binary`.

This should be treated as an optional backend, not the default.

## Suggested direction for video conversion

A fully reliable video converter without FFmpeg or FFmpeg-based libraries is not realistic for common formats like MP4, MKV, MOV, AVI and WebM.

Recommended options:

### Option A: PyAV backend

Use PyAV as the main backend.

Pros:

* avoids calling a system `ffmpeg` executable;
* exposes containers, streams, codecs and frames from Python;
* suitable for real video decoding/encoding work.

Cons:

* still depends on FFmpeg libraries;
* video conversion remains complex;
* codec availability depends on the installed/bundled build.

This is the most realistic route if the project requirement means “do not require users to install FFmpeg manually”.

### Option B: limited pure-Python/video-light mode

Support only narrow operations that do not require full transcoding:

* extract metadata when possible;
* validate file type;
* maybe extract thumbnails only if a backend supports it;
* animated image conversions, such as GIF/WebP, through Pillow where supported.

Pros:

* simpler;
* fewer compatibility issues.

Cons:

* does not satisfy real MP4/MKV/MOV/AVI/WebM transcoding.

### Option C: optional external backend

Keep the app working without FFmpeg, but allow an optional FFmpeg/Pandoc/LibreOffice backend when installed.

Example:

```text
Default mode:
- audio: Python libs
- image: Pillow
- documents: limited Python-native conversions
- video: disabled or PyAV-only

Advanced mode:
- video: FFmpeg backend if available
- documents: Pandoc/LibreOffice backend if available
```

The UI should clearly show whether a backend is available.

## Recommended next steps

1. Fix the document UI to show only supported pairs.
2. Remove unsupported document formats until a backend exists.
3. Replace `convert_office()` with `convert_document()` and route by format pair.
4. Add `convert_video()` only after choosing the backend.
5. Add `jpg` alias support for images.
6. Add alpha flattening when converting transparent images to JPEG.
7. Add tests for each supported pair.
8. Update error messages so they mention the correct converter type.
9. Return explicit “unsupported conversion” errors instead of letting random library exceptions leak into the UI.
10. Document which conversions are guaranteed, partial or intentionally unsupported.

## Notes

Audio conversion is currently the most stable part of the project.

Image conversion is usable for simple static images, but still needs edge-case handling.

Document conversion should be rebuilt around explicit format-pair support.

Video conversion should not be advertised as supported until a backend is selected and implemented.
