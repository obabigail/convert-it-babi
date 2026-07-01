# streamlit interface for the file conversion logic

# ----------------------------
# imports
# ----------------------------
import streamlit as st

from converter import FileConverter

# ----------------------------
# streamlit page configuration
# ----------------------------
st.set_page_config(
    page_title="Convert it Babi", page_icon=":material/arrow_upload_progress:"
)

# ----------------------------
# renderers for each file type
# ----------------------------


# audio
def _render_audio_converter():
    input_col, icon_col, output_col = st.columns([1.40, 0.20, 1.40])

    with input_col:
        input_formats = ["mp3", "wav", "ogg", "flac"]
        input_type = st.selectbox("Convert from", input_formats)

    with icon_col:
        st.write(":material/double_arrow:")

    with output_col:
        input_formats.remove(input_type)
        output_formats = input_formats
        output_type = st.selectbox("Convert to", output_formats)

    input_audio = st.file_uploader("Upload Audio", type=[input_type])

    if input_audio is not None:
        file_name = input_audio.name.replace(f".{input_type}", "")
        st.caption(file_name)
    else:
        return

    if st.button("Convert Audio"):
        try:
            converter = FileConverter(input_audio, input_type, output_type)
            converted = converter.convert_audio()
        except Exception as exc:
            st.error(f"Failed to convert audio: {exc}")
            return

        download_col, status_col = st.columns(2)
        with download_col:
            st.download_button(
                label="Download converted audio",
                data=converted,
                file_name=f"{file_name}.{output_type}",
                mime=f"audio/{output_type}",
            )
        with status_col:
            if converted is not None:
                st.success("Audio converted successfully!")
            else:
                st.error("Failed to convert audio.")


# video (not implemented)
def _render_video_converter():
    # input_col, icon_col, output_col = st.columns([1.40, 0.20, 1.40])

    # with input_col:
    #     input_formats = [
    #         "mp4",
    #         "mkv",
    #         "mov",
    #         "avi",
    #         "webm",
    #     ]
    #     input_type = st.selectbox("Convert from", input_formats)

    # with icon_col:
    #     st.write(":material/double_arrow:")

    # with output_col:
    #     input_formats.remove(input_type)
    #     output_formats = input_formats
    #     output_type = st.selectbox("Convert to", output_formats)

    # input_video = st.file_uploader("Upload Document", type=[input_type])

    # if input_video is None:
    #     return

    # if st.button("Convert Video"):
    #     try:
    #         converter = FileConverter(input_video, input_type, output_type)
    #         converted = converter.convert_video()
    #     except Exception as exc:
    #         st.error(f"Failed to convert video: {exc}")
    #         return

    #     download_col, status_col = st.columns(2)
    #     with download_col:
    #         st.download_button(
    #             label="Download converted video",
    #             data=converted,
    #             file_name=f"converted.{output_type}",
    #             mime=f"video/{output_type}",
    #         )
    #     with status_col:
    #         if converted is not None:
    #             st.success("Video converted successfully!")
    #         else:
    #             st.error("Failed to convert video.")
    st.info("This feature is not yet implemented.")


# image
def _render_image_converter():
    input_col, icon_col, output_col = st.columns([1.40, 0.20, 1.40])

    with input_col:
        input_formats = ["png", "jpg", "jpeg", "webp", "avif"]
        input_type = st.selectbox("Convert from", input_formats)

    with icon_col:
        st.write(":material/double_arrow:")

    with output_col:
        input_formats.remove(input_type)
        output_formats = input_formats
        output_type = st.selectbox("Convert to", output_formats)

    input_image = st.file_uploader("Upload Image", type=[input_type])

    if input_image is not None:
        file_name = input_image.name.replace(f".{input_type}", "")
        st.caption(file_name)
    else:
        return

    if st.button("Convert Image"):
        try:
            converter = FileConverter(input_image, input_type, output_type)
            converted = converter.convert_image()
        except Exception as exc:
            st.error(f"Failed to convert image: {exc}")
            return

        download_col, status_col = st.columns(2)
        with download_col:
            st.download_button(
                label="Download converted image",
                data=converted,
                file_name=f"{file_name}.{output_type}",
                mime=f"image/{output_type}",
            )
        with status_col:
            if converted is not None:
                st.success("Image converted successfully!")
            else:
                st.error("Failed to convert image.")


# documents (not implemented)
def _render_office_converter():
    st.write("Implemented in this version:")
    st.markdown(
        "<li><ol>.txt <-> .md</ol><ol>.docx <-> txt/md</ol></li>",
        unsafe_allow_html=True,
    )

    input_col, icon_col, output_col = st.columns([1.40, 0.20, 1.40])

    with input_col:
        input_formats = [
            "docx",
            "xlsx",
            "pptx",
            "pdf",
            "ods",
            "odf",
            "odt",
            "tex",
            "txt",
            "md",
        ]
        input_type = st.selectbox("Convert from", input_formats)

    with icon_col:
        st.write(":material/double_arrow:")

    with output_col:
        input_formats.remove(input_type)
        output_formats = input_formats
        output_type = st.selectbox("Convert to", output_formats)

    input_doc = st.file_uploader("Upload Document", type=[input_type])

    if input_doc is not None:
        file_name = input_doc.name.replace(f".{input_type}", "")
        st.caption(file_name)
    else:
        return

    if st.button("Convert Document"):
        try:
            converter = FileConverter(input_doc, input_type, output_type)
            converted = converter.convert_office()
        except Exception as exc:
            st.error(f"Failed to convert document: {exc}")
            return

        download_col, status_col = st.columns(2)
        with download_col:
            st.download_button(
                label="Download converted document",
                data=converted,
                file_name=f"{file_name}.{output_type}",
                mime=f"document/{output_type}",
            )
        with status_col:
            if converted is not None:
                st.success("Document converted successfully!")
            else:
                st.error("Failed to convert document.")


# ----------------------------
# main application
# ----------------------------
st.title("Convert it Babi")

with st.container():
    st.header("What do you want to convert today?")
    file_type = st.segmented_control(
        "File Type", ["Audio", "Video", "Image", "Document"], default="Audio"
    )

if file_type == "Audio":
    _render_audio_converter()

elif file_type == "Video":
    _render_video_converter()

elif file_type == "Image":
    _render_image_converter()

elif file_type == "Document":
    _render_office_converter()
