import requests
import json
from typing import Optional, Dict
import time
import toml

def load_config():
    with open("config.toml", "r") as f:
        return toml.load(f)

# Load config and assign to global variables
config = load_config()
WECOM_CORPID = config["wecom"]["corpid"]
WECOM_CORPSECRET = config["wecom"]["corpsecret"]
WECOM_AGENTID = config["wecom"]["agentid"]

class WeComMessenger:
    def __init__(self, corpid: Optional[str] = None, corpsecret: Optional[str] = None, agentid: Optional[int] = None):
        self.corpid = corpid or WECOM_CORPID
        self.corpsecret = corpsecret or WECOM_CORPSECRET
        self.agentid = agentid or WECOM_AGENTID
        self.access_token = None
        self.token_expire_at = 0
        self._get_access_token()

    def _get_access_token(self):
        """
        Get and cache access_token
        """
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corpid}&corpsecret={self.corpsecret}"
        resp = requests.get(url)
        data = resp.json()
        if data.get("errcode") == 0:
            self.access_token = data["access_token"]
            self.token_expire_at = time.time() + data["expires_in"] - 300  # Expire 5 minutes earlier
        else:
            raise Exception(f"Failed to get access_token: {data}")

    def _ensure_token(self):
        if not self.access_token or time.time() > self.token_expire_at:
            self._get_access_token()

    def send_message(self, msgtype: str, touser: Optional[str] = None, toparty: Optional[str] = None, totag: Optional[str] = None, content: Optional[Dict] = None, **kwargs):
        """
        Send WeChat Work application message
        :param msgtype: Message type, e.g. 'text', 'image', 'voice', 'video', 'file', 'textcard', 'news', 'mpnews', 'markdown', 'miniprogram_notice', 'template_card'
        :param touser: Recipient user IDs, separated by |, @all for all users
        :param toparty: Recipient department IDs, separated by |
        :param totag: Recipient tag IDs, separated by |
        :param content: Message content body, structure varies by msgtype
        :param kwargs: Other optional parameters like safe, enable_id_trans
        :return: API response
        """
        self._ensure_token()
        api_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.access_token}"
        data = {
            "msgtype": msgtype,
            "agentid": self.agentid
        }
        if touser:
            data["touser"] = touser
        if toparty:
            data["toparty"] = toparty
        if totag:
            data["totag"] = totag
        if content:
            data[msgtype] = content
        for k, v in kwargs.items():
            data[k] = v
        headers = {"Content-Type": "application/json"}
        resp = requests.post(api_url, headers=headers, data=json.dumps(data))
        return resp.json()

# Example usage
if __name__ == "__main__":
    messenger = WeComMessenger()

    # Send text message
    text_content = {
        "content": "Your package has arrived. Please bring your work card to the mail center to pick it up."
    }
    result = messenger.send_message(
        msgtype="text",
        touser="UserID1|UserID2",
        content=text_content,
        safe=0
    )
    print(result)

    # Send image message (requires uploading media first to get media_id)
    # image_content = {"media_id": "MEDIA_ID"}
    # result = messenger.send_message(msgtype="image", touser="UserID1", content=image_content)
    # print(result)

    # Other message types can be referenced in the documentation, passing different content structures
