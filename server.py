#-*- encoding:utf-8 -*-
from flask import Flask, request, Response
from xml.dom.minidom import parseString
import os
import json
import toml
import logging
import threading
from messager import WeComMessenger
from WXBizMsgCrypt3 import WXBizMsgCrypt   # https://github.com/sbzhu/weworkapi_python project URL
from callbacks import dispatch

def load_config():
    with open("config.toml", "r") as f:
        return toml.load(f)

# Load config and assign to global variables
config = load_config()
SERVER_HOST = config["server"]["host"]
SERVER_PORT = config["server"]["port"]
CALLBACK_TOKEN = config["callback"]["token"]
CALLBACK_ENCODING_AES_KEY = config["callback"]["encoding_aes_key"]
CALLBACK_CORPID = config["callback"]["corpid"]
SEND_TOKENS = config["send"]["tokens"]
SEND_TOKENS = set(SEND_TOKENS)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# URL for message callback mode in step 4. If domain is 'www.example.com', the URL in step 4 would be "http://www.example.com/hook_path"
@app.route("/recv", methods=['GET','POST']) 
def receive_message() -> Response:
    if request.method == 'GET': # Verify interface connectivity
        echo_str = signature(request, 0)
        logger.info(f"Received GET request, echo_str: {echo_str}")
        return Response(echo_str)
    elif request.method == 'POST': # Actual message receiving
        echo_str = on_message(request, 0)
        logger.info(f"Received POST request, echo_str: {echo_str}")
        return Response(echo_str)
    return Response("Method not allowed", status=405)
 
qy_api = [
    WXBizMsgCrypt(
        CALLBACK_TOKEN,
        CALLBACK_ENCODING_AES_KEY,
        CALLBACK_CORPID
    ), 
] # Corresponds to token, EncodingAESKey in message callback mode and enterprise ID

@app.route("/send", methods=['POST'])
def send_message():
    # Get request data
    data = request.get_json()
    if not data:
        return Response("No JSON data provided", status=400)
    
    # Validate required fields
    required_fields = ['to_user', 'msg', 'token']
    for field in required_fields:
        if field not in data:
            return Response(f"Missing required field: {field}", status=400)
    
    # Validate token
    if data['token'] not in SEND_TOKENS:
        return Response("Invalid token", status=401)
    
    try:
        # Initialize messenger and send message
        messenger = WeComMessenger()
        text_content = {
            "content": data['msg']
        }
        result = messenger.send_message(
            msgtype="text",
            touser=data['to_user'],
            content=text_content,
            safe=0
        )
        
        if result.get("errcode") == 0:
            resp = f'Message sent successfully, details: {json.dumps(result, indent=2)}'
            return Response(resp, status=200)
        else:
            return Response(f"Failed to send message: {result.get('errmsg')}", status=500)
            
    except Exception as e:
        return Response(f"Error sending message: {str(e)}", status=500)

# Verify interface connectivity when enabling message receiving mode
def signature(request, i): 
    msg_signature = request.args.get('msg_signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    echo_str = request.args.get('echostr', '')
    ret,sEchoStr=qy_api[i].VerifyURL(msg_signature, timestamp,nonce,echo_str)
    if ret != 0:
        logger.error("ERR: VerifyURL ret: " + str(ret))
        return "failed"
    else:
        return sEchoStr
 
# Actual message receiving
def on_message(request, i):
    msg_signature = request.args.get('msg_signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    data = request.data.decode('utf-8')
    ret,sMsg=qy_api[i].DecryptMsg(data,msg_signature, timestamp,nonce)
    if ret != 0:
        logger.error("ERR: DecryptMsg ret: " + str(ret))
        return "failed"
    else:
        doc = parseString(sMsg)
        collection = doc.documentElement
        name_xml = collection.getElementsByTagName("FromUserName")
        msg_xml = collection.getElementsByTagName("Content")
        type_xml = collection.getElementsByTagName("MsgType")
        pic_xml = collection.getElementsByTagName("PicUrl")
        msg = ""
        name = ""
        msg_type = type_xml[0].childNodes[0].data
        
        if msg_type == "text": # Text message
            name = name_xml[0].childNodes[0].data        # Sender ID
            msg = msg_xml[0].childNodes[0].data          # Message content
            logger.info(f"[ch{i}] {name}:{msg}")
            dispatch(name, msg_type, msg)
            # threading.Thread(target=os.system, args=(f"python3 command.py '{name}' '{msg}' '{i}' '0'",)).start()
            
        elif msg_type == "image": # Image message
            name = name_xml[0].childNodes[0].data
            pic_url = pic_xml[0].childNodes[0].data
            logger.info(f"[ch{i}] {name}:Image message")
            dispatch(name, msg_type, pic_url)
            # threading.Thread(target=os.system, args=(f"python3 command.py '{name}' '{pic_url}' '{i}' '1'",)).start()
 
        return "ok"
 
if __name__ == '__main__':
    app.run(SERVER_HOST, SERVER_PORT)  # Local listening port, customizable