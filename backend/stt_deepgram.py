# stt_deepgram.py

import os
import websockets
import asyncio
import json
import backoff
from .utils import setup_logging

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "36ae5b84623368e3131d163bee026d8ed7d76c4d")
DEEPGRAM_URL = "wss://api.deepgram.com/v1/listen?encoding=linear16&sample_rate=16000&channels=1&keepalive=true&keepalive_timeout=20"

logger = setup_logging()['stt']

@backoff.on_exception(backoff.expo, websockets.exceptions.ConnectionClosedError, max_tries=3)
async def connect_to_deepgram():
    if not DEEPGRAM_API_KEY:
        logger.error("DEEPGRAM_API_KEY environment variable is not set")
        raise ValueError("DEEPGRAM_API_KEY environment variable is not set")

    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}"
    }
    
    return await websockets.connect(
        DEEPGRAM_URL,
        extra_headers=headers,
        ping_interval=10,  # Send ping every 10 seconds
        ping_timeout=5    # Wait 5 seconds for pong response
    )

async def stream_to_deepgram(audio_stream):
    ws = None
    try:
        ws = await connect_to_deepgram()
        logger.info("Successfully connected to Deepgram WebSocket")
        
        last_send_time = asyncio.get_event_loop().time()
        keepalive_interval = 2  # Reduced from 5 to 2 seconds

        async for chunk in audio_stream:
            try:
                current_time = asyncio.get_event_loop().time()
                
                # If connection is closed, try to reconnect
                if not ws.open:
                    ws = await connect_to_deepgram()
                    logger.info("Reconnected to Deepgram WebSocket")

                # Send audio chunk
                await ws.send(chunk)
                last_send_time = current_time
                logger.debug(f"Sent {len(chunk)} bytes to Deepgram")

                # Receive and process response
                response = await ws.recv()
                data = json.loads(response)
                logger.debug("Received response from Deepgram")

                if "channel" in data:
                    alt = data["channel"]["alternatives"][0]
                    transcript = alt.get("transcript", "")
                    if transcript:
                        logger.info(f"Transcribed text: {transcript}")
                        yield transcript

                # Send keepalive more frequently
                if current_time - last_send_time > keepalive_interval:
                    await ws.ping()
                    last_send_time = current_time
                    logger.debug("Sent keepalive ping to Deepgram")

            except websockets.exceptions.ConnectionClosedError as e:
                logger.warning(f"Connection closed by Deepgram: {str(e)}")
                # The backoff decorator will handle reconnection
                ws = await connect_to_deepgram()
            except Exception as e:
                logger.error(f"Error processing audio chunk: {str(e)}", exc_info=True)

    except Exception as e:
        logger.error(f"Error in stream_to_deepgram: {str(e)}", exc_info=True)
        raise
    finally:
        if ws and ws.open:
            await ws.close()
