import hashlib
import hmac
import json
import random
import uuid
import datetime
import urllib.parse

import requests
from zhipuai.types.chat.chat_completion import Completion

host = "https://ecloud.10086.cn"
request_path = "/api/openapi-icp/inference-api/2128161764802560/aiops-1326615959671779328/test/service/8081//v1/chat/completions"

access_key = "xCwhDX100lhguuXCiEvpXjgAUFAW"
secret_key = "N0warDpYZUbgAgStcUlqA73vE9FwRH"
request_method = "POST"


def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H%%3A%M%%3A%SZ")


def generate_uuid():
    # str(uuid.uuid4()).replace("-", "")
    hex_digits = "0123456789abcdef"
    s = [random.choice(hex_digits) for _ in range(32)]
    s[14] = "4"  # bits 12-15 of the time_hi_and_version field to 0010
    s[19] = hex_digits[
        random.randint(0, 3) | 8
    ]  # bits 6-7 of the clock_seq_hi_and_reserved to 01
    return "".join(s)


def generate_signature(secret_key):
    signature_nonce = generate_uuid()
    signature_version = "V2.0"
    signature_method = "HmacSHA1"
    timestamp = get_timestamp()

    query_string = (
        f"AccessKey={access_key}&"
        f"SignatureMethod={signature_method}&"
        f"SignatureNonce={signature_nonce}&"
        f"SignatureVersion={signature_version}&"
        f"Timestamp={timestamp}"
    )

    sha256_hash = hashlib.sha256(query_string.encode()).hexdigest()
    encoded_request_path = request_path.replace("/", "%2F")
    before = f"{request_method}\n{encoded_request_path}\n{sha256_hash}"
    signature = hmac.new(
        key=("BC_SIGNATURE&" + secret_key).encode(),
        msg=before.encode(),
        digestmod=hashlib.sha1,
    ).hexdigest()
    return query_string, signature


def request(messages, tools) -> Completion:
    payload = {
        "model": "DeepSeek-R1-Distill-Qwen-32B",
        "messages": messages,
        "stream": False,
        "tools": tools,
    }
    headers = {"Content-Type": "application/json"}

    query_string, signature = generate_signature(secret_key)

    request_param = f"{query_string}&Signature={signature}"
    response = requests.post(
        f"{host}{request_path}?{request_param}",
        headers=headers,
        data=json.dumps(payload),
    )
    return Completion.parse_obj(response.json())
