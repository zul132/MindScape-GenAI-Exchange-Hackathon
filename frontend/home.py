import streamlit as st
from utils import setup_sidebar
import requests
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
from st_audiorec import st_audiorec
import io

st.set_page_config(page_title="MindScape", page_icon="🧠", layout="wide")

setup_sidebar()

st.title("🧠 MindScape — Diagnose. Engage. Heal.")
st.caption("⚠️ Disclaimer: Mindscape is a supportive tool for youth mental well-being and is not a medical service.")

st.subheader("Mood Check Engine")

tab1, tab2 = st.tabs(["Audio Journal", "Video Journal"])

with tab1:
    st.write("Record a short audio note about your feelings.")
    wav_audio_data = st_audiorec()

    if wav_audio_data is not None:
        st.audio(wav_audio_data, format='audio/wav')
        if st.button("Analyze my mood"):
            with st.spinner("Analyzing your mood..."):
                files = {'audio_data': ('audio.wav', wav_audio_data, 'audio/wav')}
                try:
                    response = requests.post("http://localhost:5001/analyze", files=files)
                    if response.status_code == 200:
                        results = response.json()
                        st.write("**Transcript:**", results['transcript'])
                        st.write("**Sentiment Score:**", results['sentiment_score'])
                        st.info(results['gemini_response'])
                    else:
                        st.error(f"Error from server: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Could not connect to the backend: {e}")

with tab2:
    st.write("Record a short video of yourself talking about your feelings.")

    class AudioRecorder(AudioProcessorBase):
        def __init__(self) -> None:
            self._audio_buffer = io.BytesIO()

        def recv(self, frame):
            self._audio_buffer.write(frame.to_ndarray().tobytes())
            return frame

        def get_audio(self):
            return self._audio_buffer.getvalue()

    webrtc_ctx = webrtc_streamer(
        key="video-recorder",
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=AudioRecorder,
        media_stream_constraints={"video": True, "audio": True},
    )

    if st.button("Analyze my video journal"):
        if webrtc_ctx.audio_processor:
            audio_data = webrtc_ctx.audio_processor.get_audio()
            if audio_data:
                with st.spinner("Analyzing your mood..."):
                    files = {'audio_data': ('audio.mp3', audio_data, 'audio/mp3')}
                    try:
                        response = requests.post("http://localhost:5001/analyze", files=files)
                        if response.status_code == 200:
                            results = response.json()
                            st.write("**Transcript:**", results['transcript'])
                            st.write("**Sentiment Score:**", results['sentiment_score'])
                            st.info(results['gemini_response'])
                        else:
                            st.error(f"Error from server: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Could not connect to the backend: {e}")
            else:
                st.warning("No audio was recorded.")
        else:
            st.warning("Please record a video first.")