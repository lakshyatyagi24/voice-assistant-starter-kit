import logging
import os
import sys
from datetime import datetime

# Add a filter to silence low‑level logs from the websockets library
class NoWebsocketsDebugFilter(logging.Filter):
    def filter(self, record):
        if record.name.startswith("websockets") and record.levelno < logging.WARNING:
            return False
        return True

def setup_logging():
    # Ensure stdout and stderr use UTF-8 encoding
    if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure logging
    log_filename = f'logs/voice_assistant_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    # Create a StreamHandler and add the custom filter to suppress websockets debug logs
    stream_handler = logging.StreamHandler()
    stream_handler.addFilter(NoWebsocketsDebugFilter())
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            stream_handler
        ]
    )
    
    # Create loggers for different components
    loggers = {
        'app': logging.getLogger('app'),
        'stt': logging.getLogger('stt'),
        'gpt': logging.getLogger('gpt'),
        'tts': logging.getLogger('tts')
    }
    
    return loggers