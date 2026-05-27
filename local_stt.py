"""Local speech-to-text using faster-whisper."""

import os
import tempfile
import threading

from config import (
    get_local_stt_compute_type,
    get_local_stt_device,
    get_local_stt_enabled,
    get_local_stt_model,
)
from gui_utils import log_output


class LocalSTTUnavailable(RuntimeError):
    """Raised when local STT cannot be used and caller should fallback."""


_model = None
_model_config = None
_model_lock = threading.Lock()


def _load_model():
    global _model, _model_config

    if not get_local_stt_enabled():
        raise LocalSTTUnavailable("Local STT dimatikan di konfigurasi.")

    model_size = get_local_stt_model()
    device = get_local_stt_device()
    compute_type = get_local_stt_compute_type()
    config_key = (model_size, device, compute_type)

    with _model_lock:
        if _model is not None and _model_config == config_key:
            return _model

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise LocalSTTUnavailable(
                "Library faster-whisper belum terinstall."
            ) from exc

        cpu_threads = max(2, min(os.cpu_count() or 4, 8))
        try:
            log_output(
                f"Loading local Whisper STT: model={model_size}, "
                f"device={device}, compute={compute_type}"
            )
            _model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                cpu_threads=cpu_threads,
            )
            _model_config = config_key
            return _model
        except Exception as exc:
            if device.lower() == "cpu":
                raise LocalSTTUnavailable(str(exc)) from exc

            log_output("Local STT GPU/auto gagal, mencoba fallback CPU int8...")
            try:
                _model = WhisperModel(
                    model_size,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=cpu_threads,
                )
                _model_config = (model_size, "cpu", "int8")
                return _model
            except Exception as cpu_exc:
                raise LocalSTTUnavailable(str(cpu_exc)) from cpu_exc


def transcribe_audio(audio_data, language: str = "id") -> str:
    """Transcribe SpeechRecognition AudioData with local faster-whisper."""
    model = _load_model()
    temp_path = None

    try:
        wav_bytes = audio_data.get_wav_data(convert_rate=16000, convert_width=2)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(wav_bytes)
            temp_path = temp_file.name

        segments, info = model.transcribe(
            temp_path,
            language=language,
            beam_size=1,
            vad_filter=True,
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()
        if text:
            log_output(
                f"Local STT ({info.language}, {info.language_probability:.2f}): {text}"
            )
        return text
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass
