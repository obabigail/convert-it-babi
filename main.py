# streamlit interface for the file conversion logic
import streamlit as st

from converter import FileConverter

st.set_page_config(
    page_title="Convert it Babi", page_icon=":material/arrow_upload_progress:"
)

st.title("Convert it Babi")


def _render_audio_converter():
    input_col, icon_col, output_col = st.columns([1.40, 0.20, 1.40])

    with input_col:
        input_type = st.selectbox("Convert from", ["mp3", "wav", "ogg", "flac"])

    with icon_col:
        st.write(":material/double_arrow:")

    with output_col:
        output_type = st.selectbox(
            "Convert to",
            (
                ["mp3", "wav", "ogg", "flac"]
                if input_type != "mp3"
                else ["wav", "ogg", "flac"]
            ),
        )

    input_audio = st.file_uploader("Upload Audio", type=[input_type])

    if input_audio is None:
        return

    if st.button("Convert Audio"):
        converter = FileConverter(input_audio, input_type, output_type)
        converted = converter.convert_audio()

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


with st.container():
    st.header("What do you want to convert today?")
    file_type = st.segmented_control(
        "File Type", ["Audio", "Video", "Image", "Document"], default="Audio"
    )

if file_type == "Audio":
    _render_audio_converter()
else:
    pass
