# gpt_response.py

import openai
import os
from .utils import setup_logging

logger = setup_logging()['gpt']

openai.api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL", "gpt-4")

# Optional function GPT can call
functions = [
    {
        "name": "get_current_time",
        "description": "Returns the current server time",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

def get_current_time():
    from datetime import datetime
    logger.debug("get_current_time function called")
    return {"time": datetime.now().isoformat()}

function_map = {
    "get_current_time": get_current_time
}

def call_function_by_name(name):
    logger.debug(f"Attempting to call function: {name}")
    if name in function_map:
        result = function_map[name]()
        logger.info(f"Function {name} executed successfully")
        return result
    logger.warning(f"Function {name} not found")
    return {"error": "Function not found"}

def ask_gpt(message: str) -> str:
    logger.info(f"Sending request to GPT with message: {message}")
    try:
        if not openai.api_key:
            logger.error("OPENAI_API_KEY environment variable is not set")
            return "[GPT Error] OpenAI API key is not set"

        logger.debug(f"Using model: {model}")
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": message}],
            functions=functions,
            function_call="auto"
        )

        choice = response.choices[0]
        logger.debug(f"Received response from GPT with finish_reason: {choice.finish_reason}")

        # If GPT calls a function
        if choice.finish_reason == "function_call":
            function_name = choice.message.function_call.name
            logger.info(f"GPT requested function call: {function_name}")
            result = call_function_by_name(function_name)
            return f"[Function: {function_name}] → {result['time']}"

        logger.info("GPT provided direct response")
        return choice.message.content

    except Exception as e:
        logger.error(f"Error in ask_gpt: {str(e)}", exc_info=True)
        return f"[GPT Error] {str(e)}"
