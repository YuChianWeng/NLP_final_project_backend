import azure.cognitiveservices.speech as speechsdk

from app.config import settings


class TtsUnavailable(Exception):
    """TTS 服務不可用"""
    pass


def synthesize(text: str) -> bytes:
    """
    將文字轉換成 MP3 bytes
    """

    if not text:
        raise TtsUnavailable("empty text")

    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_API_KEY,
            region=settings.AZURE_SPEECH_REGION
        )

        speech_config.speech_synthesis_voice_name = (
            settings.AZURE_SPEECH_VOICE_NAME
        )

        result = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None
        ).speak_text_async(text).get()

        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Reason:", result.reason)
            print("Details:", result.cancellation_details)
            raise TtsUnavailable("speech synthesis failed")

        return result.audio_data

    except Exception as e:
        raise TtsUnavailable(str(e))