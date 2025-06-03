import logging

from handler_wzx import handler_wzx

logger = logging.getLogger(__name__)

def dispatch(name, msg_type, msg):
    if name == "wzx":
        handler_wzx(msg_type, msg)
        return
    logger.warning(f"Unknown user: {name}")
    return