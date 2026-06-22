# streamlit interface for the file conversion logic

# imports
import streamlit as st

from converter import FileConverter

# streamlit page configuration
st.set_page_config(
    page_title="Convert it Babi", page_icon=":material/arrow_upload_progress:"
)


# renderers for each file type
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

    if input_audio is None:
        return

    if st.button("Convert Audio"):
        try:
            converter = FileConverter(input_audio, input_type, output_type)
            converted = converter.convert_audio()
        except Exception as exc:
            st.error(f"Failed to convert image: {exc}")
            return

        download_col, status_col = st.columns(2)
        with download_col:
            st.download_button(
                label="Download converted audio",
                data=converted,
                file_name=f"converted.{output_type}",
                mime=f"audio/{output_type}",
            )
        with status_col:
            if converted is not None:
                st.success("Audio converted successfully!")
            else:
                st.error("Failed to convert audio.")


def _render_image_converter():
    input_col, icon_col, output_col = st.columns([1.40, 0.20, 1.40])

    with input_col:
        input_formats = ["png", "jpeg", "webp", "avif"]
        input_type = st.selectbox("Convert from", input_formats)

    with icon_col:
        st.write(":material/double_arrow:")

    with output_col:
        input_formats.remove(input_type)
        output_formats = input_formats
        output_type = st.selectbox("Convert to", output_formats)

    input_image = st.file_uploader("Upload Image", type=[input_type])

    if input_image is None:
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
                file_name=f"converted.{output_type}",
                mime=f"image/{output_type}",
            )
        with status_col:
            if converted is not None:
                st.success("Image converted successfully!")
            else:
                st.error("Failed to convert image.")


st.title("Convert it Babi")

with st.container():
    st.header("What do you want to convert today?")
    file_type = st.segmented_control(
        "File Type", ["Audio", "Video", "Image", "Document"], default="Audio"
    )

if file_type == "Audio":
    _render_audio_converter()

elif file_type == "Image":
    _render_image_converter()
