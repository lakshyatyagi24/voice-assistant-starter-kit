# app.py

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from starlette.websockets import WebSocketDisconnect
import uvicorn
import asyncio
from .stt_deepgram import stream_to_deepgram
from .gpt_response import ask_gpt
from .tts_azure import synthesize_speech
from .utils import setup_logging

app = FastAPI()
loggers = setup_logging()
logger = loggers['app']

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection opened")

    audio_stream = asyncio.Queue()
    client_id = id(websocket)  # Unique identifier for the client
    logger.debug(f"Created audio stream for client {client_id}")

    async def audio_receiver():
        try:
            while True:
                data = await websocket.receive_bytes()
                logger.debug(f"Received {len(data)} bytes of audio from client {client_id}")
                await audio_stream.put(data)
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for client {client_id}")
            await audio_stream.put(None)
        except Exception as e:
            logger.error(f"Error in audio receiver for client {client_id}: {str(e)}", exc_info=True)
            await audio_stream.put(None)

    async def pipeline():
        try:
            async for transcript in stream_to_deepgram(audio_stream_iterator()):
                logger.info(f"[User {client_id}]: {transcript}")
                reply = ask_gpt(transcript)
                logger.info(f"[Assistant -> User {client_id}]: {reply}")
                
                logger.debug("Synthesizing speech response")
                path = synthesize_speech(reply, f"response_{client_id}.mp3")
                
                with open(path, "rb") as f:
                    audio_bytes = f.read()
                logger.debug(f"Sending {len(audio_bytes)} bytes of audio response to client {client_id}")
                await websocket.send_bytes(audio_bytes)
        except Exception as e:
            logger.error(f"Error in pipeline for client {client_id}: {str(e)}", exc_info=True)

    async def audio_stream_iterator():
        while True:
            try:
                chunk = await audio_stream.get()
                if chunk is None:
                    logger.debug(f"Audio stream ended for client {client_id}")
                    break
                yield chunk
            except Exception as e:
                logger.error(f"Error in audio stream iterator for client {client_id}: {str(e)}", exc_info=True)
                break

    try:
        await asyncio.gather(audio_receiver(), pipeline())
    except Exception as e:
        logger.error(f"Error in main websocket handler for client {client_id}: {str(e)}", exc_info=True)

@app.get("/")
async def index():
    logger.debug("Index page requested")
    return HTMLResponse("<h1>Voice Assistant Backend Running 🎙️</h1>")

if __name__ == "__main__":
    logger.info("Starting Voice Assistant backend server")
    uvicorn.run(app, host="0.0.0.0", port=8765)
