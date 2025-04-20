# tts_azure.py

import os
import requests
from .utils import setup_logging

logger = setup_logging()['tts']

AZURE_TTS_KEY = os.getenv("AZURE_TTS_KEY")
AZURE_REGION = os.getenv("AZURE_TTS_REGION")
VOICE_NAME = os.getenv("AZURE_TTS_VOICE", "en-US-JennyNeural")

def synthesize_speech(text: str, output_path: str = "output.mp3"):
    logger.info(f"Starting speech synthesis for text: {text}")
    
    if not AZURE_TTS_KEY or not AZURE_REGION:
        logger.error("Missing Azure TTS credentials")
        raise Exception("Missing Azure TTS credentials.")

    url = f"https://{AZURE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    logger.debug(f"Using Azure TTS endpoint: {url}")

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_TTS_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
        "User-Agent": "VoiceAssistant"
    }

    ssml = f"""
    <speak version='1.0' xml:lang='en-US'>
        <voice name='{VOICE_NAME}'>{text}</voice>
    </speak>
    """
    
    logger.debug(f"Using voice: {VOICE_NAME}")
    
    try:
        logger.debug("Sending request to Azure TTS")
        response = requests.post(url, headers=headers, data=ssml.encode("utf-8"))

        if response.status_code == 200:
            logger.info(f"Successfully synthesized speech, saving to {output_path}")
            with open(output_path, "wb") as f:
                f.write(response.content)
            return output_path
        else:
            error_msg = f"TTS failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
    except Exception as e:
        logger.error(f"Error in speech synthesis: {str(e)}", exc_info=True)
        raise
