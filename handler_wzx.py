import logging
import toml
from openai import OpenAI
from messager import WeComMessenger

def load_config():
    with open("config.toml", "r") as f:
        return toml.load(f)

config = load_config()
OPENAI_API_KEY = config["openai"]["api_key"]
OPENAI_BASE_URL = config["openai"]["base_url"]
OPENAI_MODEL = config["openai"]["model"]

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

logger = logging.getLogger(__name__)

def handler_wzx(msg_type, msg):
    if msg_type == "text":
        logger.debug(f"Handling text message: {msg}")
        handle_text(msg)
    elif msg_type == "image":
        logger.debug(f"Handling image message: {msg}")
    else:
        logger.warning(f"Unknown message type: {msg_type}")
    return

def handle_text(msg):
    match msg:
        case _:
            do_chat(msg)
    return

def do_chat(msg):
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": msg}
        ]
        logger.info(f"Invoking OpenAI API with model {OPENAI_MODEL}, messages: {messages}")
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages
        )
        reply = response.choices[0].message.content
        logger.info(f"Chat response: {reply}")
        messenger = WeComMessenger()
        result = messenger.send_message(
            msgtype="text",
            touser="wzx",
            content={"content": reply}
        )
        logger.debug(f"Send message result: {result}")
        assert result.get("errcode") == 0, f"Failed to send message: {result.get('errmsg')}"
    except Exception as e:
        logger.error(f"Error in do_chat: {e}")
    return